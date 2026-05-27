"""
Review & Rating routes for doctor consultations.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..utils.decorators import role_required
from ..services import review_service

review_bp = Blueprint("review", __name__)


@review_bp.route("/create", methods=["POST"])
@jwt_required()
@role_required("patient")
def create():
    """POST /api/reviews/create"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    consultation_id = data.get("consultation_id")
    rating = data.get("rating")
    comment = data.get("comment")

    if consultation_id is None or rating is None:
        return jsonify({"error": "consultation_id and rating are required"}), 400

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be an integer"}), 400

    try:
        review = review_service.create_review(
            patient_id=user.id,
            consultation_id=int(consultation_id),
            rating=rating,
            comment=comment,
        )
        return jsonify({"success": True, "review": review.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@review_bp.route("/doctor/<int:doctor_id>", methods=["GET"])
@jwt_required()
def doctor_reviews(doctor_id):
    """GET /api/reviews/doctor/<id>"""
    reviews = review_service.get_doctor_reviews(doctor_id)
    return jsonify({"success": True, "reviews": [r.to_dict() for r in reviews]}), 200


@review_bp.route("/doctor/<int:doctor_id>/summary", methods=["GET"])
@jwt_required()
def doctor_summary(doctor_id):
    """GET /api/reviews/doctor/<id>/summary"""
    summary = review_service.get_doctor_rating_summary(doctor_id)
    return jsonify({"success": True, "summary": summary}), 200
