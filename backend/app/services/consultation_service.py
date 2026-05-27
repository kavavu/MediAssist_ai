"""Consultation service: priority assignment, doctor matching, CRUD operations."""
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Consultation, User, FollowUp
from ..utils.symptom_utils import (
    normalize_symptoms, generate_ai_insight,
    generate_acknowledgement, generate_advice,
    generate_suggested_tests, generate_urgency,
    extract_severity_from_text,
)
from .openai_service import generate_doctor_response
from ..utils.time_format import format_time_ago
import logging

from ..sockets.emitters import (
    emit_new_consultation,
    emit_consultation_update,
    emit_new_message,
)

logger = logging.getLogger(__name__)

# ============================================================
# SECTION 8 — IMPROVED SPECIALIZATION MAPPING
# ============================================================

_CONDITION_SPECIALIZATION_MAP: Dict[str, str] = {
    "malaria": "General Doctor", "typhoid": "General Doctor", "dengue": "General Doctor",
    "tuberculosis": "General Doctor", "common cold": "General Doctor", "flu": "General Doctor",
    "pneumonia": "General Doctor", "covid": "General Doctor", "fever": "General Doctor",
    "diabetes": "Endocrinologist", "hypothyroidism": "Endocrinologist", "hyperthyroidism": "Endocrinologist",
    "asthma": "Pulmonologist", "bronchitis": "Pulmonologist", "copd": "Pulmonologist",
    "respiratory": "Pulmonologist", "persistent cough": "Pulmonologist", "wheezing": "Pulmonologist",
    "hypertension": "Cardiologist", "heart disease": "Cardiologist", "heart attack": "Cardiologist",
    "cardiac": "Cardiologist", "chest pain": "Cardiologist", "palpitations": "Cardiologist",
    "migraine": "Neurologist", "epilepsy": "Neurologist", "stroke": "Neurologist",
    "parkinson": "Neurologist", "severe headache": "Neurologist", "seizure": "Neurologist",
    "confusion": "Neurologist", "slurred speech": "Neurologist", "weakness of one body side": "Neurologist",
    "gerd": "Gastroenterologist", "gastroenteritis": "Gastroenterologist",
    "peptic ulcer": "Gastroenterologist", "jaundice": "Gastroenterologist", "hepatitis": "Gastroenterologist",
    "abdominal pain": "Gastroenterologist", "vomiting": "Gastroenterologist", "diarrhea": "Gastroenterologist",
    "acne": "Dermatologist", "psoriasis": "Dermatologist", "eczema": "Dermatologist",
    "skin": "Dermatologist", "skin rash": "Dermatologist", "itching": "Dermatologist",
    "blister": "Dermatologist", "blackheads": "Dermatologist",
    "arthritis": "Orthopedic", "osteoporosis": "Orthopedic", "joint pain": "Orthopedic",
    "knee pain": "Orthopedic", "hip joint pain": "Orthopedic", "back pain": "Orthopedic",
    "neck pain": "Orthopedic", "movement stiffness": "Orthopedic",
    "chronic kidney disease": "Nephrologist", "kidney": "Nephrologist",
    "blood in urine": "Nephrologist", "burning micturition": "Nephrologist",
    "depression": "Psychiatrist", "anxiety": "Psychiatrist", "suicide": "Psychiatrist",
    "cancer": "Oncologist", "tumor": "Oncologist",
    # Fallback category mappings
    "cardiovascular": "Cardiologist",
    "respiratory": "Pulmonologist",
    "gastrointestinal": "Gastroenterologist",
    "dermatological": "Dermatologist",
    "neurological": "Neurologist",
    "psychiatric": "Psychiatrist",
    "endocrine": "Endocrinologist",
}

# ============================================================
# SECTION 7 — IMPROVED PRIORITY ASSIGNMENT
# ============================================================

_SEVERE_KEYWORDS = {
    "chest pain", "severe pain", "difficulty breathing", "shortness of breath",
    "unconscious", "fainting", "seizure", "bleeding", "vomiting blood",
    "blood in stool", "high fever", "severe headache", "paralysis",
    "heart attack", "stroke", "suicide", "allergic reaction", "anaphylaxis",
    "poisoning", "overdose", "trauma", "fracture", "burn",
    "unresponsive", "coma", "altered sensorium", "slurred speech",
    "weakness of one body side", "severe weakness", "severe bleeding",
    "cant breathe", "can't breathe", "gasping", "blue lips",
}

_MODERATE_KEYWORDS = {
    "fever", "vomiting", "weakness", "dizziness", "nausea", "diarrhea",
    "cough", "sore throat", "body ache", "joint pain", "back pain",
    "abdominal pain", "headache", "fatigue", "loss of appetite",
    "chills", "sweating", "dehydration", "wheezing", "congestion",
    "persistent cough", "burning micturition", "blood in urine",
    "muscle pain", "stiff neck", "confusion", "palpitations",
}

# High-risk combinations that force HIGH priority even if individual keywords are moderate
_HIGH_RISK_COMBINATIONS = [
    {"chest pain", "shortness of breath"},
    {"chest pain", "difficulty breathing"},
    {"chest pain", "dizziness"},
    {"chest pain", "palpitations"},
    {"chest pain", "sweating"},
    {"severe headache", "stiff neck"},
    {"severe headache", "confusion"},
    {"fever", "stiff neck", "confusion"},
    {"vomiting", "severe headache", "confusion"},
    {"unconscious", "seizure"},
    {"weakness of one body side", "slurred speech"},
    {"weakness of one body side", "confusion"},
    {"high fever", "rash"},
    {"high fever", "bleeding"},
]


def _normalize(text: Optional[str]) -> str:
    return (text or "").lower().strip()


def determine_priority(symptoms: str, predicted_condition: Optional[str] = None, confidence_score: Optional[float] = None) -> str:
    """
    Determine consultation priority using:
    - severe keyword detection in raw symptoms
    - moderate keyword detection in raw symptoms
    - high-risk symptom combinations in raw symptoms
    - severity phrase extraction
    - predicted condition only used if confidence is reasonable (>= 0.40)
    """
    text = _normalize(symptoms)
    # Only trust predicted condition for priority if confidence is decent
    condition_text = _normalize(predicted_condition) if (confidence_score is not None and confidence_score >= 0.40) else ""
    combined = text + " " + condition_text

    # Check high-risk combinations first (primarily on raw symptoms)
    symptom_set = set(s.strip() for s in text.replace(",", " ").split())
    for combo in _HIGH_RISK_COMBINATIONS:
        if combo.issubset(symptom_set):
            return "HIGH"
        # Also check substring matching for multi-word combos
        matched = 0
        for phrase in combo:
            if phrase in text:
                matched += 1
        if matched >= len(combo):
            return "HIGH"

    # Severe keywords (check raw symptoms first, then combined if high confidence)
    for keyword in _SEVERE_KEYWORDS:
        if keyword in text:
            return "HIGH"
    if condition_text:
        for keyword in _SEVERE_KEYWORDS:
            if keyword in condition_text:
                return "HIGH"

    # Moderate keywords
    for keyword in _MODERATE_KEYWORDS:
        if keyword in text:
            return "MEDIUM"

    # Severity phrase extraction
    severity = extract_severity_from_text(symptoms)
    if severity in ("severe", "sudden"):
        return "HIGH"
    if severity in ("moderate", "persistent"):
        return "MEDIUM"

    return "LOW"


def match_specialization(predicted_condition: Optional[str], confidence_score: Optional[float] = None, symptoms: Optional[str] = None) -> str:
    """
    Match a predicted condition to a doctor specialization.
    Falls back to General Doctor if no match or if confidence is very low.
    For red-flag or low-confidence cases, infers specialization from symptoms when possible.
    """
    condition = _normalize(predicted_condition)

    # If confidence is decent, trust the predicted condition
    if confidence_score is not None and confidence_score >= 0.20 and condition:
        for key, spec in _CONDITION_SPECIALIZATION_MAP.items():
            if key in condition:
                return spec

    # Low confidence or no condition: try to infer from symptoms
    if symptoms:
        text = _normalize(symptoms)
        # Cardiovascular red flags
        if any(k in text for k in ("chest pain", "shortness of breath", "difficulty breathing", "palpitations", "heart racing", "racing heart")):
            return "Cardiologist"
        # Neurological red flags
        if any(k in text for k in ("seizure", "severe headache", "stiff neck", "confusion", "slurred speech", "weakness of one body side", "loss of consciousness", "passing out", "passed out")):
            return "Neurologist"
        # Respiratory
        if any(k in text for k in ("persistent cough", "wheezing", "shortness of breath", "difficulty breathing")):
            return "Pulmonologist"
        # Dermatological
        if any(k in text for k in ("skin rash", "itching", "red spots", "blister", "blackheads")):
            return "Dermatologist"
        # Gastrointestinal
        if any(k in text for k in ("vomiting", "diarrhea", "abdominal pain", "stomach pain", "blood in stool", "jaundice")):
            return "Gastroenterologist"
        # Urinary / renal
        if any(k in text for k in ("blood in urine", "burning micturition", "pain when peeing")):
            return "Nephrologist"
        # Psychiatric
        if any(k in text for k in ("depression", "anxiety", "suicide", "suicidal")):
            return "Psychiatrist"
        # Endocrine
        if any(k in text for k in ("diabetes", "thyroid", "weight gain", "weight loss", "excessive hunger", "polyuria")):
            return "Endocrinologist"
        # Orthopedic
        if any(k in text for k in ("joint pain", "knee pain", "hip joint pain", "back pain", "neck pain", "movement stiffness", "swelling joints")):
            return "Orthopedic"

    # Final fallback
    return "General Doctor"


def find_best_doctor(specialization: str, preferred_doctor_id: Optional[int] = None) -> Optional[User]:
    """
    Smart doctor selection with load balancing.
    1. If preferred_doctor_id is provided and valid, use it (patient override).
    2. Match specialization, prefer available doctors, sort by least load.
    3. Fallback: General doctors → any doctor.
    """
    # Step 0: Patient override — if a preferred doctor is specified and valid and verified
    if preferred_doctor_id:
        preferred = User.query.filter_by(id=preferred_doctor_id, role="doctor", is_verified=True).first()
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


def create_consultation(
    patient_id: int,
    symptoms: str,
    predicted_condition: Optional[str],
    message: Optional[str],
    confidence_score: Optional[float] = None,
    preferred_doctor_id: Optional[int] = None,
) -> Tuple[Consultation, str]:
    priority = determine_priority(symptoms, predicted_condition, confidence_score)
    specialization = match_specialization(predicted_condition, confidence_score, symptoms)
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

    # Increment doctor load atomically using UPDATE to prevent race conditions
    try:
        db.session.flush()  # Ensure consultation gets an ID before commit
        db.session.execute(
            db.update(User)
            .where(User.id == doctor.id)
            .values(current_load=User.current_load + 1)
        )
        db.session.commit()
        db.session.refresh(consultation)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"[DB] Failed to create consultation: {e}")
        raise ValueError("Failed to create consultation. Please try again.") from e

    # Emit real-time event to the assigned doctor (non-blocking; DB is source of truth)
    try:
        emit_new_consultation(doctor.id, consultation.to_dict())
    except Exception as e:
        logger.error(f"[Socket] Failed to emit new_consultation for doctor {doctor.id}: {e}")

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
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")
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
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"[DB] Failed to respond to consultation: {e}")
        raise ValueError("Failed to submit response. Please try again.") from e

    # Emit real-time update to the consultation room (patient will see it)
    try:
        emit_consultation_update(consultation.id, consultation.to_dict())
    except Exception as e:
        logger.error(f"[Socket] Failed to emit consultation_updated for consultation {consultation.id}: {e}")

    return consultation


def resolve_consultation(consultation_id: int, doctor_id: int) -> Consultation:
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")
    if consultation.doctor_id != doctor_id:
        raise PermissionError("You are not assigned to this consultation.")
    if consultation.status == "resolved":
        raise ValueError("Consultation is already resolved.")

    consultation.status = "resolved"
    consultation.resolved_at = datetime.utcnow()

    # Decrement doctor load atomically using UPDATE to prevent race conditions
    try:
        db.session.execute(
            db.update(User)
            .where(User.id == doctor_id)
            .values(current_load=db.func.greatest(0, User.current_load - 1))
        )
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"[DB] Failed to resolve consultation: {e}")
        raise ValueError("Failed to resolve consultation. Please try again.") from e

    # Emit real-time update to the consultation room
    try:
        emit_consultation_update(consultation.id, consultation.to_dict())
    except Exception as e:
        logger.error(f"[Socket] Failed to emit consultation_updated for consultation {consultation.id}: {e}")

    return consultation


def get_consultation_by_id(consultation_id: int) -> Optional[Consultation]:
    return Consultation.query.get(consultation_id)


def generate_ai_response(consultation_id: int, doctor_id: int) -> Dict:
    """Auto-generate structured response suggestions for a doctor."""
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")
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


def generate_ai_full_response(consultation_id: int, doctor_id: int) -> Dict:
    """Generate a complete, human-like AI-assisted doctor response using OpenAI."""
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")
    if consultation.doctor_id != doctor_id:
        raise PermissionError("You are not assigned to this consultation.")

    symptoms = consultation.symptoms_clean or consultation.symptoms
    condition = consultation.predicted_condition
    priority = consultation.priority

    # Build inputs grounded in clinical engine output
    urgency_text = generate_urgency(priority)
    tests_text = generate_suggested_tests(condition)
    insight_data = generate_ai_insight(condition, symptoms, priority)
    ai_insight = insight_data.get("insight", "")

    result = generate_doctor_response(
        predicted_condition=condition,
        severity=priority,
        symptoms=symptoms,
        urgency=urgency_text,
        recommended_tests=tests_text,
        ai_insight=ai_insight,
        patient_message=consultation.message,
    )

    return {
        "full_response": result["response"],
        "source": result["source"],
        "structured": {
            "acknowledgement": generate_acknowledgement(symptoms, condition),
            "advice": generate_advice(condition, priority),
            "tests": tests_text,
            "urgency": urgency_text,
        },
    }


def edit_response(
    consultation_id: int, doctor_id: int,
    acknowledgement: Optional[str] = None,
    advice: Optional[str] = None,
    tests: Optional[str] = None,
    urgency: Optional[str] = None,
) -> Consultation:
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")
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
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"[DB] Failed to edit response: {e}")
        raise ValueError("Failed to update response. Please try again.") from e

    # Emit real-time update to the consultation room
    try:
        emit_consultation_update(consultation.id, consultation.to_dict())
    except Exception as e:
        logger.error(f"[Socket] Failed to emit consultation_updated for consultation {consultation.id}: {e}")

    return consultation


def add_followup(consultation_id: int, sender_id: int, sender_role: str, message: str) -> Dict:
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")

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
    try:
        db.session.commit()
        db.session.refresh(followup)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"[DB] Failed to add followup: {e}")
        raise ValueError("Failed to send message. Please try again.") from e

    # Emit real-time message to the consultation room
    try:
        emit_new_message(consultation.id, followup.to_dict())
    except Exception as e:
        logger.error(f"[Socket] Failed to emit new_message for consultation {consultation.id}: {e}")

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


def get_recommended_doctor(condition: Optional[str] = None, confidence_score: Optional[float] = None, symptoms: Optional[str] = None) -> Optional[Dict]:
    """Get the recommended doctor for a given condition using smart assignment."""
    specialization = match_specialization(condition, confidence_score, symptoms)
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
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        raise ValueError("Consultation not found")
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
