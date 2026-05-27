"""
Admin routes for the MediAssist AI platform.
All routes are protected by JWT and require admin role.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..models import User
from ..extensions import db
from ..services import admin_service

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required(fn):
    """Decorator that ensures the current user has the 'admin' role."""
    from functools import wraps
    from flask_jwt_extended import get_current_user

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != "admin":
            return {"error": "Admin access required"}, 403
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Dashboard Analytics
# ---------------------------------------------------------------------------
@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@admin_required
def get_dashboard():
    """GET /api/admin/dashboard — comprehensive admin dashboard stats."""
    try:
        stats = admin_service.get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Doctor Management
# ---------------------------------------------------------------------------
@admin_bp.route("/doctors", methods=["GET"])
@jwt_required()
@admin_required
def list_doctors():
    """GET /api/admin/doctors — list all doctors with stats."""
    try:
        doctors = admin_service.get_all_doctors()
        return jsonify(doctors), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@admin_bp.route("/doctors/<int:doctor_id>/verify", methods=["POST"])
@jwt_required()
@admin_required
def verify_doctor(doctor_id):
    """POST /api/admin/doctors/<id>/verify — verify a doctor."""
    try:
        admin_service.verify_doctor(doctor_id, verified=True)
        return jsonify({"message": "Doctor verified successfully"}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@admin_bp.route("/doctors/<int:doctor_id>/unverify", methods=["POST"])
@jwt_required()
@admin_required
def unverify_doctor(doctor_id):
    """POST /api/admin/doctors/<id>/unverify — unverify a doctor."""
    try:
        admin_service.verify_doctor(doctor_id, verified=False)
        return jsonify({"message": "Doctor unverified successfully"}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@admin_bp.route("/doctors/<int:doctor_id>/availability", methods=["POST"])
@jwt_required()
@admin_required
def toggle_availability(doctor_id):
    """POST /api/admin/doctors/<id>/availability — toggle doctor availability."""
    try:
        doctor = admin_service.toggle_doctor_availability(doctor_id)
        return jsonify({
            "message": "Availability toggled",
            "is_available": doctor.is_available,
        }), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# User & Patient Management
# ---------------------------------------------------------------------------
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def list_users():
    """GET /api/admin/users — list all non-admin users."""
    try:
        users = admin_service.get_all_users()
        return jsonify(users), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@admin_bp.route("/patients", methods=["GET"])
@jwt_required()
@admin_required
def list_patients():
    """GET /api/admin/patients — list all patients."""
    try:
        patients = admin_service.get_all_patients()
        return jsonify(patients), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Consultation Management
# ---------------------------------------------------------------------------
@admin_bp.route("/consultations", methods=["GET"])
@jwt_required()
@admin_required
def list_consultations():
    """GET /api/admin/consultations — list all consultations."""
    try:
        consultations = admin_service.get_all_consultations()
        return jsonify(consultations), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Payment Analytics
# ---------------------------------------------------------------------------
@admin_bp.route("/payments", methods=["GET"])
@jwt_required()
@admin_required
def list_payments():
    """GET /api/admin/payments — payment history and analytics."""
    try:
        data = admin_service.get_payment_analytics()
        return jsonify(data), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Review Analytics
# ---------------------------------------------------------------------------
@admin_bp.route("/reviews", methods=["GET"])
@jwt_required()
@admin_required
def list_reviews():
    """GET /api/admin/reviews — review analytics and history."""
    try:
        data = admin_service.get_review_analytics()
        return jsonify(data), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Legacy endpoints (keep for backward compatibility with existing frontend)
# ---------------------------------------------------------------------------
# Legacy endpoints removed to prevent duplicate/conflicting routes.
# Use /api/admin/doctors (filter is_verified=False) and /api/admin/doctors/<id>/verify instead.
