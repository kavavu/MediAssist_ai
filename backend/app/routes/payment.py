"""
Payment routes for demo/simulation payment processing.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..utils.decorators import role_required
from ..services import payment_service

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/create", methods=["POST"])
@jwt_required()
def create():
    """POST /api/payments/create"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    payment_method = data.get("payment_method", "M-Pesa")
    appointment_id = data.get("appointment_id")
    order_id = data.get("order_id")

    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a positive number"}), 400

    try:
        payment = payment_service.create_payment(
            user_id=user.id,
            amount=amount,
            payment_method=payment_method,
            appointment_id=int(appointment_id) if appointment_id is not None else None,
            order_id=int(order_id) if order_id is not None else None,
        )
        return jsonify({"success": True, "payment": payment.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@payment_bp.route("/<int:payment_id>/complete", methods=["POST"])
@jwt_required()
def complete(payment_id):
    """POST /api/payments/<id>/complete"""
    user = get_current_user()
    try:
        payment = payment_service.complete_payment(payment_id, user.id)
        return jsonify({"success": True, "payment": payment.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@payment_bp.route("/my-payments", methods=["GET"])
@jwt_required()
def my_payments():
    """GET /api/payments/my-payments"""
    user = get_current_user()
    payments = payment_service.get_user_payments(user.id)
    return jsonify({"success": True, "payments": [p.to_dict() for p in payments]}), 200
