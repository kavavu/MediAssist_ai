from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Consultation
from app.extensions import db

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "admin":
            return {"error": "Admin access required"}, 403

        return fn(*args, **kwargs)

    return wrapper


@admin_bp.route("/doctors/pending", methods=["GET"])
@jwt_required()
@admin_required
def get_pending_doctors():
    doctors = User.query.filter_by(role="doctor", is_verified=False).all()

    return jsonify([
        {
            "id": d.id,
            "name": d.name,
            "email": d.email,
            "specialization": d.specialization
        } for d in doctors
    ])


@admin_bp.route("/doctors/<int:doctor_id>/approve", methods=["POST"])
@jwt_required()
@admin_required
def approve_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)

    doctor.is_verified = True
    db.session.commit()

    return {"message": "Doctor approved"}


@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
@admin_required
def get_admin_analytics():
    total_users = User.query.count()
    total_doctors = User.query.filter_by(role="doctor").count()
    total_patients = User.query.filter_by(role="patient").count()
    total_consultations = Consultation.query.count()

    return {
        "total_users": total_users,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_consultations": total_consultations
    }
