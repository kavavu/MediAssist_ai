"""
Appointment routes for booking and managing patient-doctor appointments.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..utils.decorators import role_required
from ..services import appointment_service

appointment_bp = Blueprint("appointment", __name__)


@appointment_bp.route("/appointments/doctor/<int:doctor_id>/available-slots", methods=["GET"])
@jwt_required()
def available_slots(doctor_id):
    """GET /api/appointments/doctor/<id>/available-slots?date=YYYY-MM-DD"""
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Missing 'date' query parameter"}), 400
    try:
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    slots = appointment_service.get_available_slots(doctor_id, appointment_date)
    return jsonify({"success": True, "slots": slots}), 200


@appointment_bp.route("/appointments/book", methods=["POST"])
@jwt_required()
@role_required("patient")
def book():
    """POST /api/appointments/book"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    doctor_id = data.get("doctor_id")
    date_str = data.get("appointment_date")
    time_str = data.get("appointment_time")
    notes = data.get("notes")

    if not doctor_id or not date_str or not time_str:
        return jsonify({"error": "doctor_id, appointment_date, and appointment_time are required"}), 400

    try:
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        appointment = appointment_service.create_appointment(
            patient_id=user.id,
            doctor_id=int(doctor_id),
            appointment_date=appointment_date,
            appointment_time=time_str.strip(),
            notes=notes,
        )
        return jsonify({"success": True, "appointment": appointment.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@appointment_bp.route("/appointments/patient", methods=["GET"])
@jwt_required()
@role_required("patient")
def patient_appointments():
    """GET /api/appointments/patient"""
    user = get_current_user()
    appointments = appointment_service.get_patient_appointments(user.id)
    return jsonify({"success": True, "appointments": [a.to_dict() for a in appointments]}), 200


@appointment_bp.route("/appointments/doctor", methods=["GET"])
@jwt_required()
@role_required("doctor")
def doctor_appointments():
    """GET /api/appointments/doctor"""
    user = get_current_user()
    appointments = appointment_service.get_doctor_appointments(user.id)
    return jsonify({"success": True, "appointments": [a.to_dict() for a in appointments]}), 200


@appointment_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@jwt_required()
def cancel(appointment_id):
    """POST /api/appointments/<id>/cancel"""
    user = get_current_user()
    if user.role not in ("patient", "doctor"):
        return jsonify({"error": "Insufficient permissions"}), 403

    try:
        appointment = appointment_service.cancel_appointment(appointment_id, user.id, user.role)
        return jsonify({"success": True, "appointment": appointment.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
