"""
Consultation API routes.

Endpoints:
    POST   /api/consultation/create          — patient creates consultation
    GET    /api/consultation/patient          — patient lists their consultations
    GET    /api/consultation/doctor           — doctor lists assigned consultations
    POST   /api/consultation/respond/<id>     — doctor responds to consultation
    POST   /api/consultation/respond/<id>/edit — doctor edits an existing response
    POST   /api/consultation/followup/<id>    — doctor sends a follow-up message
    POST   /api/consultation/resolve/<id>     — doctor marks as resolved
    GET    /api/consultation/stats            — doctor dashboard analytics
    GET    /api/consultation/ai-response/<id> — get AI-generated response suggestions
    GET    /api/consultation/history/<id>     — get full consultation history
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..utils.decorators import role_required
from ..utils.time_format import format_time_ago
from ..services import consultation_service

consultation_bp = Blueprint("consultation", __name__)


def _enrich(consultation):
    data = consultation.to_dict()
    data["created_at_relative"] = format_time_ago(consultation.created_at)
    data["responded_at_relative"] = format_time_ago(consultation.responded_at)
    data["resolved_at_relative"] = format_time_ago(consultation.resolved_at)
    return data


@consultation_bp.route("/create", methods=["POST"])
@jwt_required()
@role_required("patient")
def create_consultation():
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    symptoms = (data.get("symptoms") or "").strip()
    if not symptoms:
        return jsonify({"error": "Symptoms are required."}), 400

    predicted_condition = (data.get("predicted_condition") or "").strip() or None
    message = (data.get("message") or "").strip() or None
    confidence_score = data.get("confidence_score")

    preferred_doctor_id = data.get("preferred_doctor_id")
    if preferred_doctor_id:
        try:
            preferred_doctor_id = int(preferred_doctor_id)
        except (ValueError, TypeError):
            preferred_doctor_id = None

    try:
        consultation, info = consultation_service.create_consultation(
            patient_id=user.id,
            symptoms=symptoms,
            predicted_condition=predicted_condition,
            message=message,
            confidence_score=confidence_score,
            preferred_doctor_id=preferred_doctor_id,
        )
        return jsonify({
            "success": True,
            "consultation": _enrich(consultation),
            "info": info,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create consultation: {str(e)}"}), 500


@consultation_bp.route("/patient", methods=["GET"])
@jwt_required()
@role_required("patient")
def list_patient_consultations():
    user = get_current_user()
    consultations = consultation_service.get_patient_consultations(user.id)
    return jsonify({
        "consultations": [_enrich(c) for c in consultations],
    }), 200


@consultation_bp.route("/doctor", methods=["GET"])
@jwt_required()
@role_required("doctor")
def list_doctor_consultations():
    user = get_current_user()
    consultations = consultation_service.get_doctor_consultations(user.id)
    return jsonify({
        "consultations": [_enrich(c) for c in consultations],
    }), 200


@consultation_bp.route("/respond/<int:consultation_id>", methods=["POST"])
@jwt_required()
@role_required("doctor")
def respond_to_consultation(consultation_id):
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    has_any_field = any([
        data.get("response"),
        data.get("acknowledgement"),
        data.get("advice"),
        data.get("tests"),
        data.get("urgency"),
    ])
    if not has_any_field:
        return jsonify({"error": "At least one response field is required."}), 400

    try:
        consultation = consultation_service.respond_to_consultation(
            consultation_id=consultation_id,
            doctor_id=user.id,
            response_text=data.get("response"),
            acknowledgement=data.get("acknowledgement"),
            advice=data.get("advice"),
            tests=data.get("tests"),
            urgency=data.get("urgency"),
        )
        return jsonify({
            "success": True,
            "consultation": _enrich(consultation),
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to respond: {str(e)}"}), 500


@consultation_bp.route("/resolve/<int:consultation_id>", methods=["POST"])
@jwt_required()
@role_required("doctor")
def resolve_consultation(consultation_id):
    user = get_current_user()
    try:
        consultation = consultation_service.resolve_consultation(consultation_id, user.id)
        return jsonify({
            "success": True,
            "consultation": _enrich(consultation),
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to resolve: {str(e)}"}), 500


@consultation_bp.route("/stats", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_doctor_stats():
    user = get_current_user()
    stats = consultation_service.get_consultation_stats(user.id)
    return jsonify({"stats": stats}), 200


@consultation_bp.route("/ai-response/<int:consultation_id>", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_ai_response(consultation_id):
    user = get_current_user()
    try:
        suggestions = consultation_service.generate_ai_response(consultation_id, user.id)
        return jsonify({
            "success": True,
            "suggestions": suggestions,
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to generate: {str(e)}"}), 500


@consultation_bp.route("/respond/<int:consultation_id>/edit", methods=["POST"])
@jwt_required()
@role_required("doctor")
def edit_response(consultation_id):
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    has_any_field = any([
        data.get("acknowledgement"),
        data.get("advice"),
        data.get("tests"),
        data.get("urgency"),
    ])
    if not has_any_field:
        return jsonify({"error": "At least one response field is required."}), 400

    try:
        consultation = consultation_service.edit_response(
            consultation_id=consultation_id,
            doctor_id=user.id,
            acknowledgement=data.get("acknowledgement"),
            advice=data.get("advice"),
            tests=data.get("tests"),
            urgency=data.get("urgency"),
        )
        return jsonify({
            "success": True,
            "consultation": _enrich(consultation),
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to edit response: {str(e)}"}), 500


@consultation_bp.route("/followup/<int:consultation_id>", methods=["POST"])
@jwt_required()
def send_followup(consultation_id):
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    sender_role = data.get("sender_role") or user.role
    if not message:
        return jsonify({"error": "Follow-up message is required."}), 400
    if sender_role not in ("doctor", "patient"):
        return jsonify({"error": "Invalid sender role."}), 400

    try:
        followup = consultation_service.add_followup(
            consultation_id=consultation_id,
            sender_id=user.id,
            sender_role=sender_role,
            message=message,
        )
        return jsonify({
            "success": True,
            "followup": followup,
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to send follow-up: {str(e)}"}), 500


@consultation_bp.route("/history/<int:consultation_id>", methods=["GET"])
@jwt_required()
def get_history(consultation_id):
    user = get_current_user()
    try:
        history = consultation_service.get_consultation_history(
            consultation_id=consultation_id,
            user_id=user.id,
        )
        return jsonify({
            "success": True,
            "history": history,
        }), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to load history: {str(e)}"}), 500


@consultation_bp.route("/doctors/preview", methods=["GET"])
@jwt_required()
@role_required("patient")
def get_doctors_preview():
    """Return available doctors for patient to preview before creating consultation."""
    try:
        doctors = consultation_service.get_doctors_for_preview()
        return jsonify({"doctors": doctors}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load doctors: {str(e)}"}), 500


@consultation_bp.route("/doctors/<int:doctor_id>/stats", methods=["GET"])
@jwt_required()
@role_required("patient")
def get_doctor_public_stats(doctor_id):
    """Return public stats for a specific doctor (for patient transparency)."""
    try:
        stats = consultation_service.get_doctor_public_stats(doctor_id)
        return jsonify({"stats": stats}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to load doctor stats: {str(e)}"}), 500


@consultation_bp.route("/doctors/recommend", methods=["GET"])
@jwt_required()
@role_required("patient")
def get_recommended_doctor():
    """Return the recommended doctor based on condition + load balancing."""
    condition = request.args.get("condition", "").strip()
    try:
        recommendation = consultation_service.get_recommended_doctor(condition)
        return jsonify({"recommendation": recommendation}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get recommendation: {str(e)}"}), 500
