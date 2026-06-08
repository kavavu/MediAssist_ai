"""
Payment routes for M-Pesa Daraja integration.

Endpoints:
- POST /api/payments/create          — create a payment record
- POST /api/payments/<id>/stk-push   — initiate STK push
- GET  /api/payments/<id>/status     — poll payment status
- POST /api/payments/<id>/complete   — legacy simulation complete
- GET  /api/payments/my-payments     — user payment history
- POST /api/payments/mpesa/callback  — M-Pesa Daraja callback
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..services import payment_service
from ..services.mpesa_service import process_callback, normalize_phone, is_valid_kenyan_phone
from ..extensions import db
from ..models import Payment
from ..utils.decorators import role_required

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
    phone_number = data.get("phone_number")

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
            phone_number=phone_number,
        )
        return jsonify({"success": True, "payment": payment.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@payment_bp.route("/<int:payment_id>/stk-push", methods=["POST"])
@jwt_required()
def stk_push(payment_id):
    """POST /api/payments/<id>/stk-push — initiate M-Pesa STK Push."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    phone_number = data.get("phone_number")

    try:
        result = payment_service.initiate_mpesa_stk(
            payment_id=payment_id,
            phone_number=phone_number,
        )
        return jsonify({
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "checkout_request_id": result.get("checkout_request_id"),
            "merchant_request_id": result.get("merchant_request_id"),
        }), 200 if result.get("success") else 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"STK push failed: {exc}"}), 500


@payment_bp.route("/<int:payment_id>/status", methods=["GET"])
@jwt_required()
def payment_status(payment_id):
    """GET /api/payments/<id>/status — poll current payment status."""
    user = get_current_user()
    try:
        data = payment_service.query_payment_status(payment_id, user.id)
        return jsonify({"success": True, "payment": data}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@payment_bp.route("/<int:payment_id>/complete", methods=["POST"])
@jwt_required()
@role_required("admin")
def complete(payment_id):
    """
    POST /api/payments/<id>/complete — admin-only manual completion.
    
    SECURITY: This endpoint allows manually marking a payment as complete
    WITHOUT M-Pesa confirmation. It is restricted to admin users only.
    In production, this should typically be disabled or heavily audited.
    """
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


@payment_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """
    POST /api/payments/mpesa/callback
    Receives M-Pesa STK Push callback from Safaricom.
    """
    data = request.get_json(silent=True) or {}
    try:
        result = process_callback(data)
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Callback processed successfully",
        }), 200
    except Exception as exc:
        # Always return 200 to Safaricom so they don't retry aggressively
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Accepted",
        }), 200
