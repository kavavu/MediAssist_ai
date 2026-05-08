"""Consultation service: priority assignment, doctor matching, CRUD operations."""
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..extensions import db
from ..models import Consultation, User, FollowUp
from ..utils.symptom_utils import (
    normalize_symptoms, generate_ai_insight,
    generate_acknowledgement, generate_advice,
    generate_suggested_tests, generate_urgency,
)
from ..utils.time_format import format_time_ago
from ..sockets.emitters import (
    emit_new_consultation,
    emit_consultation_update,
    emit_new_message,
)

_CONDITION_SPECIALIZATION_MAP: Dict[str, str] = {
    "malaria": "General Doctor", "typhoid": "General Doctor", "dengue": "General Doctor",
    "tuberculosis": "General Doctor", "common cold": "General Doctor", "flu": "General Doctor",
    "pneumonia": "General Doctor", "covid": "General Doctor", "fever": "General Doctor",
    "diabetes": "Endocrinologist", "hypothyroidism": "Endocrinologist", "hyperthyroidism": "Endocrinologist",
    "asthma": "Pulmonologist", "bronchitis": "Pulmonologist", "copd": "Pulmonologist",
    "respiratory": "Pulmonologist",
    "hypertension": "Cardiologist", "heart disease": "Cardiologist", "heart attack": "Cardiologist",
    "cardiac": "Cardiologist",
    "migraine": "Neurologist", "epilepsy": "Neurologist", "stroke": "Neurologist",
    "parkinson": "Neurologist",
    "gerd": "Gastroenterologist", "gastroenteritis": "Gastroenterologist",
    "peptic ulcer": "Gastroenterologist", "jaundice": "Gastroenterologist", "hepatitis": "Gastroenterologist",
    "acne": "Dermatologist", "psoriasis": "Dermatologist", "eczema": "Dermatologist", "skin": "Dermatologist",
    "arthritis": "Orthopedic", "osteoporosis": "Orthopedic",
    "chronic kidney disease": "Nephrologist", "kidney": "Nephrologist",
    "depression": "Psychiatrist", "anxiety": "Psychiatrist",
    "cancer": "Oncologist",
}

_SEVERE_KEYWORDS = {
    "chest pain", "severe pain", "difficulty breathing", "shortness of breath",
    "unconscious", "fainting", "seizure", "bleeding", "vomiting blood",
    "blood in stool", "high fever", "severe headache", "paralysis",
    "heart attack", "stroke", "suicide", "allergic reaction", "anaphylaxis",
    "poisoning", "overdose", "trauma", "fracture", "burn",
}

_MODERATE_KEYWORDS = {
    "fever", "vomiting", "weakness", "dizziness", "nausea", "diarrhea",
    "cough", "sore throat", "body ache", "joint pain", "back pain",
    "abdominal pain", "headache", "fatigue", "loss of appetite",
    "chills", "sweating", "dehydration", "wheezing", "congestion",
}


def _normalize(text: Optional[str]) -> str:
    return (text or "").lower().strip()


def determine_priority(symptoms: str, predicted_condition: Optional[str] = None) -> str:
    combined = _normalize(symptoms) + " " + _normalize(predicted_condition)
    for keyword in _SEVERE_KEYWORDS:
        if keyword in combined:
            return "HIGH"
    for keyword in _MODERATE_KEYWORDS:
        if keyword in combined:
            return "MEDIUM"
    return "LOW"


def match_specialization(predicted_condition: Optional[str]) -> str:
    condition = _normalize(predicted_condition)
    if not condition:
        return "General Doctor"
    for key, spec in _CONDITION_SPECIALIZATION_MAP.items():
        if key in condition:
            return spec
    return "General Doctor"


def find_best_doctor(specialization: str, preferred_doctor_id: Optional[int] = None) -> Optional[User]:
    """
    Smart doctor selection with load balancing.
    1. If preferred_doctor_id is provided and valid, use it (patient override).
    2. Match specialization, prefer available doctors, sort by least load.
    3. Fallback: General doctors → any doctor.
    """
    # Step 0: Patient override — if a preferred doctor is specified and valid
    if preferred_doctor_id:
        preferred = User.query.filter_by(id=preferred_doctor_id, role="doctor").first()
        if preferred:
            return preferred

    # Step 1: Get verified doctors with matching specialization
    doctors = (
        User.query.filter_by(role="doctor", is_verified=True)
        .filter(db.func.lower(User.specialization) == db.func.lower(specialization))
        .all()
    )

    # Step 2: Filter available doctors
    available_doctors = [d for d in doctors if d.is_available]

    # Step 3: Prefer available doctors
    candidates = available_doctors if available_doctors else doctors

    # Step 4: Sort by least load
    candidates.sort(key=lambda d: d.current_load)

    # Step 5: Return least busy doctor
    if candidates:
        return candidates[0]

    # Step 6: Fallback → General doctors (verified only)
    if specialization.lower() != "general doctor":
        general_doctors = (
            User.query.filter_by(role="doctor", is_verified=True)
            .filter(db.func.lower(User.specialization) == "general doctor")
            .all()
        )
        if general_doctors:
            general_available = [d for d in general_doctors if d.is_available]
            general_candidates = general_available if general_available else general_doctors
            general_candidates.sort(key=lambda d: d.current_load)
            return general_candidates[0]

    # Step 7: Final fallback → any verified doctor
    any_doctors = User.query.filter_by(role="doctor", is_verified=True).all()
    if any_doctors:
        any_available = [d for d in any_doctors if d.is_available]
        any_candidates = any_available if any_available else any_doctors
        any_candidates.sort(key=lambda d: d.current_load)
        return any_candidates[0]

    return None


def find_matching_doctor(specialization: str) -> Optional[User]:
    """Backward-compatible wrapper around find_best_doctor."""
    return find_best_doctor(specialization)


def create_consultation(
    patient_id: int,
    symptoms: str,
    predicted_condition: Optional[str],
    message: Optional[str],
    confidence_score: Optional[float] = None,
    preferred_doctor_id: Optional[int] = None,
) -> Tuple[Consultation, str]:
    priority = determine_priority(symptoms, predicted_condition)
    specialization = match_specialization(predicted_condition)
    doctor = find_best_doctor(specialization, preferred_doctor_id=preferred_doctor_id)

    if doctor is None:
        raise ValueError("No doctor is available in the system. Please contact admin.")

    symptoms_clean = normalize_symptoms(symptoms)
    ai_data = generate_ai_insight(predicted_condition, symptoms_clean, priority)

    consultation = Consultation(
        patient_id=patient_id,
        doctor_id=doctor.id,
        symptoms=symptoms,
        symptoms_clean=symptoms_clean,
        predicted_condition=predicted_condition,
        confidence_score=confidence_score,
        message=message,
        priority=priority,
        status="pending",
        ai_insight=ai_data["insight"],
        ai_risk_level=ai_data["risk_level"],
        ai_suggested_steps=ai_data["suggested_steps"],
    )
    db.session.add(consultation)
    db.session.commit()

    # Increment doctor load after assignment
    doctor.current_load += 1
    db.session.commit()

    # Emit real-time event to the assigned doctor
    emit_new_consultation(doctor.id, consultation.to_dict())

    info = f"Priority: {priority} | Assigned to Dr. {doctor.name} ({doctor.specialization or 'General Doctor'})"
    return consultation, info


def get_patient_consultations(patient_id: int) -> List[Consultation]:
    return (
        Consultation.query.filter_by(patient_id=patient_id)
        .order_by(Consultation.created_at.desc())
        .all()
    )


def get_doctor_consultations(doctor_id: int) -> List[Consultation]:
    priority_order = db.case(
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2},
        value=Consultation.priority,
    )
    return (
        Consultation.query.filter_by(doctor_id=doctor_id)
        .order_by(priority_order, Consultation.created_at.desc())
        .all()
    )


def get_consultation_stats(doctor_id: int) -> Dict:
    from datetime import date
    today = date.today()
    total_today = Consultation.query.filter(
        Consultation.doctor_id == doctor_id,
        db.func.date(Consultation.created_at) == today,
    ).count()
    pending = Consultation.query.filter_by(doctor_id=doctor_id, status="pending").count()
    high_severity = Consultation.query.filter_by(doctor_id=doctor_id, priority="HIGH").count()
    responded = Consultation.query.filter(
        Consultation.doctor_id == doctor_id,
        Consultation.status == "responded",
        Consultation.responded_at.isnot(None),
    ).all()
    avg_response_minutes = 0
    if responded:
        total_seconds = sum(
            (c.responded_at - c.created_at).total_seconds()
            for c in responded
        )
        avg_response_minutes = int(total_seconds / len(responded) / 60)
    return {
        "total_patients_today": total_today,
        "pending_cases": pending,
        "high_severity_cases": high_severity,
        "average_response_minutes": avg_response_minutes,
    }


def respond_to_consultation(
    consultation_id: int, doctor_id: int,
    response_text: Optional[str] = None,
    acknowledgement: Optional[str] = None,
    advice: Optional[str] = None,
    tests: Optional[str] = None,
    urgency: Optional[str] = None,
) -> Consultation:
    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.doctor_id != doctor_id:
        raise PermissionError("You are not assigned to this consultation.")
    if consultation.status == "resolved":
        raise ValueError("This consultation has been resolved.")

    if acknowledgement:
        consultation.response_acknowledgement = acknowledgement
    if advice:
        consultation.response_advice = advice
    if tests:
        consultation.response_tests = tests
    if urgency:
        consultation.response_urgency = urgency
    if response_text:
        consultation.doctor_response = response_text

    consultation.status = "responded"
    consultation.responded_at = datetime.utcnow()
    db.session.commit()

    # Emit real-time update to the consultation room (patient will see it)
    emit_consultation_update(consultation.id, consultation.to_dict())

    return consultation


def resolve_consultation(consultation_id: int, doctor_id: int) -> Consultation:
    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.doctor_id != doctor_id:
        raise PermissionError("You are not assigned to this consultation.")
    consultation.status = "resolved"
    consultation.resolved_at = datetime.utcnow()
    db.session.commit()

    # Decrement doctor load, ensuring it never goes below 0
    doctor = User.query.get(doctor_id)
    if doctor:
        doctor.current_load = max(0, doctor.current_load - 1)
        db.session.commit()

    # Emit real-time update to the consultation room
    emit_consultation_update(consultation.id, consultation.to_dict())

    return consultation


def get_consultation_by_id(consultation_id: int) -> Optional[Consultation]:
    return Consultation.query.get(consultation_id)


def generate_ai_response(consultation_id: int, doctor_id: int) -> Dict:
    """Auto-generate structured response suggestions for a doctor."""
    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.doctor_id != doctor_id:
        raise PermissionError("You are not assigned to this consultation.")

    symptoms = consultation.symptoms_clean or consultation.symptoms
    condition = consultation.predicted_condition
    priority = consultation.priority

    return {
        "acknowledgement": generate_acknowledgement(symptoms, condition),
        "advice": generate_advice(condition, priority),
        "tests": generate_suggested_tests(condition),
        "urgency": generate_urgency(priority),
    }


def edit_response(
    consultation_id: int, doctor_id: int,
    acknowledgement: Optional[str] = None,
    advice: Optional[str] = None,
    tests: Optional[str] = None,
    urgency: Optional[str] = None,
) -> Consultation:
    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.doctor_id != doctor_id:
        raise PermissionError("You are not assigned to this consultation.")
    if consultation.status not in ("responded", "resolved"):
        raise ValueError("Cannot edit a response that has not been submitted yet.")

    if acknowledgement is not None:
        consultation.response_acknowledgement = acknowledgement.strip() or None
    if advice is not None:
        consultation.response_advice = advice.strip() or None
    if tests is not None:
        consultation.response_tests = tests.strip() or None
    if urgency is not None:
        consultation.response_urgency = urgency.strip() or None

    consultation.responded_at = datetime.utcnow()
    db.session.commit()

    # Emit real-time update to the consultation room
    emit_consultation_update(consultation.id, consultation.to_dict())

    return consultation


def add_followup(consultation_id: int, sender_id: int, sender_role: str, message: str) -> Dict:
    consultation = Consultation.query.get_or_404(consultation_id)
    
    # Validate sender is part of this consultation
    if sender_role == "doctor" and consultation.doctor_id != sender_id:
        raise PermissionError("You are not assigned to this consultation.")
    if sender_role == "patient" and consultation.patient_id != sender_id:
        raise PermissionError("You are not the patient for this consultation.")
    
    followup = FollowUp(
        consultation_id=consultation_id,
        sender_role=sender_role,
        sender_id=sender_id,
        message=message.strip(),
    )
    db.session.add(followup)
    db.session.commit()

    # Emit real-time message to the consultation room
    emit_new_message(consultation.id, followup.to_dict())

    return followup.to_dict()


def get_doctors_for_preview() -> List[Dict]:
    """Return all verified doctors for patient selection preview."""
    doctors = User.query.filter_by(role="doctor", is_verified=True).all()
    # Sort by least load for better UX
    doctors.sort(key=lambda d: d.current_load)
    return [
        {
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization or "General Doctor",
            "email": d.email,
            "is_available": d.is_available,
            "current_load": d.current_load,
            "is_verified": d.is_verified,
        }
        for d in doctors
    ]


def get_doctor_public_stats(doctor_id: int) -> Dict:
    """Return public-facing stats for a doctor (patient transparency)."""
    doctor = User.query.filter_by(id=doctor_id, role="doctor", is_verified=True).first()
    if not doctor:
        raise ValueError("Doctor not found")

    from datetime import date, timedelta

    today = date.today()
    week_ago = today - timedelta(days=7)

    total_consultations = Consultation.query.filter_by(doctor_id=doctor_id).count()
    total_responded = Consultation.query.filter_by(doctor_id=doctor_id, status="responded").count()
    total_resolved = Consultation.query.filter_by(doctor_id=doctor_id, status="resolved").count()

    # Response time calculation
    responded = Consultation.query.filter(
        Consultation.doctor_id == doctor_id,
        Consultation.status.in_(["responded", "resolved"]),
        Consultation.responded_at.isnot(None),
    ).all()

    avg_response_minutes = 0
    if responded:
        total_seconds = sum(
            (c.responded_at - c.created_at).total_seconds()
            for c in responded
        )
        avg_response_minutes = int(total_seconds / len(responded) / 60)

    # Recent activity (last 7 days)
    recent_count = Consultation.query.filter(
        Consultation.doctor_id == doctor_id,
        db.func.date(Consultation.created_at) >= week_ago,
    ).count()

    return {
        "doctor_id": doctor.id,
        "doctor_name": doctor.name,
        "specialization": doctor.specialization or "General Doctor",
        "is_available": doctor.is_available,
        "current_load": doctor.current_load,
        "total_consultations": total_consultations,
        "total_responded": total_responded,
        "total_resolved": total_resolved,
        "average_response_minutes": avg_response_minutes,
        "recent_patients_7d": recent_count,
    }


def get_recommended_doctor(condition: Optional[str] = None) -> Optional[Dict]:
    """Get the recommended doctor for a given condition using smart assignment."""
    specialization = match_specialization(condition)
    doctor = find_best_doctor(specialization)

    if not doctor:
        return None

    # Get additional stats for the recommendation
    stats = get_doctor_public_stats(doctor.id)

    return {
        "doctor": {
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization or "General Doctor",
            "is_available": doctor.is_available,
            "current_load": doctor.current_load,
        },
        "matched_specialization": specialization,
        "reason": f"Best match: {specialization} with lowest patient load",
        "stats": stats,
    }


def get_consultation_history(consultation_id: int, user_id: int) -> List[Dict]:
    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.patient_id != user_id and consultation.doctor_id != user_id:
        raise PermissionError("You do not have access to this consultation.")

    history = []
    # Initial creation event
    history.append({
        "type": "created",
        "timestamp": consultation.created_at.isoformat() if consultation.created_at else None,
        "timestamp_relative": format_time_ago(consultation.created_at),
        "data": {
            "symptoms": consultation.symptoms_clean or consultation.symptoms,
            "predicted_condition": consultation.predicted_condition,
            "confidence_score": consultation.confidence_score,
            "message": consultation.message,
            "priority": consultation.priority,
        },
    })

    # Response event
    if consultation.status in ("responded", "resolved") and consultation.responded_at:
        history.append({
            "type": "responded",
            "timestamp": consultation.responded_at.isoformat() if consultation.responded_at else None,
            "timestamp_relative": format_time_ago(consultation.responded_at),
            "data": {
                "acknowledgement": consultation.response_acknowledgement,
                "advice": consultation.response_advice,
                "tests": consultation.response_tests,
                "urgency": consultation.response_urgency,
            },
        })

    # Resolution event
    if consultation.status == "resolved" and consultation.resolved_at:
        history.append({
            "type": "resolved",
            "timestamp": consultation.resolved_at.isoformat() if consultation.resolved_at else None,
            "timestamp_relative": format_time_ago(consultation.resolved_at),
            "data": {},
        })

    # Follow-ups
    for f in consultation.followups:
        history.append({
            "type": "followup",
            "timestamp": f.created_at.isoformat() if f.created_at else None,
            "timestamp_relative": format_time_ago(f.created_at),
            "data": {
                "sender_role": f.sender_role,
                "sender_name": f.sender.name if f.sender else None,
                "message": f.message,
            },
        })

    history.sort(key=lambda x: x["timestamp"] or "")
    return history
