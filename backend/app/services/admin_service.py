"""
Admin service layer for the admin dashboard.
All business logic for admin operations lives here.
"""
from sqlalchemy import func
from ..extensions import db
from ..models import User, Consultation, Payment, Review, Appointment


def get_dashboard_stats():
    """Return comprehensive dashboard statistics for the admin panel."""
    total_users = User.query.count()
    total_patients = User.query.filter_by(role="patient").count()
    total_doctors = User.query.filter_by(role="doctor").count()
    verified_doctors = User.query.filter_by(role="doctor", is_verified=True).count()
    pending_doctors = User.query.filter_by(role="doctor", is_verified=False).count()

    total_consultations = Consultation.query.count()
    pending_consultations = Consultation.query.filter_by(status="pending").count()
    resolved_consultations = Consultation.query.filter_by(status="resolved").count()

    total_payments = Payment.query.count()
    completed_payments = Payment.query.filter_by(status="completed").count()

    revenue_row = db.session.query(func.sum(Payment.amount)).filter(Payment.status == "completed").scalar()
    total_revenue = float(revenue_row) if revenue_row is not None else 0.0

    total_appointments = Appointment.query.count()
    active_doctors = User.query.filter_by(role="doctor", is_available=True).count()

    avg_rating_row = db.session.query(func.avg(Review.rating)).scalar()
    average_doctor_rating = round(float(avg_rating_row), 2) if avg_rating_row is not None else 0.0

    return {
        "total_users": total_users,
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "verified_doctors": verified_doctors,
        "pending_doctors": pending_doctors,
        "total_consultations": total_consultations,
        "pending_consultations": pending_consultations,
        "resolved_consultations": resolved_consultations,
        "total_payments": total_payments,
        "completed_payments": completed_payments,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "active_doctors": active_doctors,
        "average_doctor_rating": average_doctor_rating,
    }


def get_all_doctors():
    """Return all doctors with verification status, workload, and availability."""
    doctors = User.query.filter_by(role="doctor").order_by(User.created_at.desc()).all()
    result = []
    for d in doctors:
        rating_row = db.session.query(func.avg(Review.rating)).filter(Review.doctor_id == d.id).scalar()
        avg_rating = round(float(rating_row), 2) if rating_row is not None else 0.0
        result.append({
            "id": d.id,
            "name": d.name,
            "email": d.email,
            "specialization": d.specialization,
            "is_verified": d.is_verified,
            "is_available": d.is_available,
            "current_load": d.current_load,
            "rating": avg_rating,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return result


def verify_doctor(doctor_id: int, verified: bool = True):
    """Set a doctor's verification status."""
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        raise ValueError("Doctor not found")
    doctor.is_verified = verified
    db.session.commit()
    return doctor


def toggle_doctor_availability(doctor_id: int):
    """Toggle a doctor's availability flag."""
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        raise ValueError("Doctor not found")
    doctor.is_available = not doctor.is_available
    db.session.commit()
    return doctor


def get_all_users():
    """Return all non-admin users (patients and doctors) with basic stats."""
    users = User.query.filter(User.role != "admin").order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        consultation_count = Consultation.query.filter(
            (Consultation.patient_id == u.id) | (Consultation.doctor_id == u.id)
        ).count()
        appointment_count = Appointment.query.filter(
            (Appointment.patient_id == u.id) | (Appointment.doctor_id == u.id)
        ).count()
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "specialization": u.specialization,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "consultation_count": consultation_count,
            "appointment_count": appointment_count,
        })
    return result


def get_all_patients():
    """Return all patients with basic stats."""
    patients = User.query.filter_by(role="patient").order_by(User.created_at.desc()).all()
    result = []
    for p in patients:
        consultation_count = Consultation.query.filter_by(patient_id=p.id).count()
        appointment_count = Appointment.query.filter_by(patient_id=p.id).count()
        result.append({
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "consultation_count": consultation_count,
            "appointment_count": appointment_count,
        })
    return result


def get_all_consultations():
    """Return all consultations with patient and doctor info."""
    consultations = Consultation.query.order_by(Consultation.created_at.desc()).all()
    return [c.to_dict(include_response=False) for c in consultations]


def get_payment_analytics():
    """Return payment history, revenue totals, and method breakdown."""
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    payment_list = [p.to_dict() for p in payments]

    total_revenue = db.session.query(func.sum(Payment.amount)).filter(Payment.status == "completed").scalar()
    total_revenue = float(total_revenue) if total_revenue is not None else 0.0

    completed = Payment.query.filter_by(status="completed").count()
    failed = Payment.query.filter_by(status="failed").count()
    pending = Payment.query.filter_by(status="pending").count()

    method_breakdown = []
    methods = db.session.query(Payment.payment_method, func.count(Payment.id), func.sum(Payment.amount)) \
        .filter(Payment.status == "completed") \
        .group_by(Payment.payment_method).all()
    for method, count, amount in methods:
        method_breakdown.append({
            "method": method,
            "count": count,
            "amount": float(amount) if amount is not None else 0.0,
        })

    return {
        "payments": payment_list,
        "total_revenue": total_revenue,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "method_breakdown": method_breakdown,
    }


def get_review_analytics():
    """Return all reviews, doctor ratings, average platform rating, and recent reviews."""
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    review_list = [r.to_dict(include_names=True) for r in reviews]

    avg_platform = db.session.query(func.avg(Review.rating)).scalar()
    average_platform_rating = round(float(avg_platform), 2) if avg_platform is not None else 0.0

    # Top rated doctors (min 1 review)
    doctor_ratings = db.session.query(
        Review.doctor_id,
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).group_by(Review.doctor_id).order_by(func.avg(Review.rating).desc()).all()

    top_doctors = []
    for doctor_id, avg_rating, review_count in doctor_ratings:
        doctor = User.query.get(doctor_id)
        if doctor:
            top_doctors.append({
                "id": doctor.id,
                "name": doctor.name,
                "specialization": doctor.specialization,
                "avg_rating": round(float(avg_rating), 2),
                "review_count": review_count,
            })

    recent_reviews = review_list[:10]

    return {
        "reviews": review_list,
        "average_platform_rating": average_platform_rating,
        "top_doctors": top_doctors,
        "recent_reviews": recent_reviews,
    }
