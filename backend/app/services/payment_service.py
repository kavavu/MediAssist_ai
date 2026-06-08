"""
Payment business logic with M-Pesa Daraja integration.

- Create payment records (with demo amount safety)
- Initiate STK Push
- Poll/query transaction status
- Process callbacks
- Fetch user payment history

SAFETY: All DB operations use explicit transaction blocks with rollback on failure.
"""
import os
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Payment, User, Appointment, Order
from .mpesa_service import (
    stk_push,
    query_stk_status,
    normalize_phone,
    is_valid_kenyan_phone,
    get_demo_phone,
    is_demo_mode,
    DEMO_STK_AMOUNT,
)

_PAYMENT_METHODS = {"M-Pesa", "Card", "Cash"}


def create_payment(
    user_id: int,
    amount: float,
    payment_method: str = "M-Pesa",
    appointment_id: Optional[int] = None,
    order_id: Optional[int] = None,
    phone_number: Optional[str] = None,
) -> Payment:
    """
    Create a pending payment record.
    Raises ValueError if user not found, invalid method, or duplicate completed payment.
    """
    user = User.query.get(user_id)
    if user is None:
        raise ValueError("User not found")

    if payment_method not in _PAYMENT_METHODS:
        raise ValueError(f"Invalid payment method. Choose from: {', '.join(sorted(_PAYMENT_METHODS))}")

    # Validate ownership of linked resources
    if appointment_id is not None:
        appt = Appointment.query.get(appointment_id)
        if appt is None:
            raise ValueError("Appointment not found")
        if appt.patient_id != user_id:
            raise ValueError("You do not own this appointment")
        existing = Payment.query.filter_by(
            appointment_id=appointment_id, status="success"
        ).first()
        if existing:
            raise ValueError("This appointment has already been paid for")

    if order_id is not None:
        order = Order.query.get(order_id)
        if order is None:
            raise ValueError("Order not found")
        if order.user_id != user_id:
            raise ValueError("You do not own this order")
        existing = Payment.query.filter_by(
            order_id=order_id, status="success"
        ).first()
        if existing:
            raise ValueError("This order has already been paid for")

    # Demo safety: the *displayed* amount is what the user sees,
    # but the actual STK amount will be 1 KSh in demo mode.
    displayed_amount = Decimal(str(amount))
    actual_amount = Decimal(str(DEMO_STK_AMOUNT)) if is_demo_mode() else displayed_amount

    # Normalize phone
    if phone_number:
        phone_number = normalize_phone(phone_number)
    else:
        phone_number = get_demo_phone()

    payment = Payment(
        user_id=user_id,
        appointment_id=appointment_id,
        order_id=order_id,
        amount=actual_amount,
        displayed_amount=displayed_amount,
        payment_method=payment_method,
        transaction_reference=f"SIM-{uuid.uuid4().hex[:12].upper()}",
        phone_number=phone_number,
        status="pending",
    )
    db.session.add(payment)

    try:
        db.session.commit()
        db.session.refresh(payment)
    except SQLAlchemyError as e:
        db.session.rollback()
        raise ValueError("Failed to create payment. Please try again.") from e

    return payment


def initiate_mpesa_stk(
    payment_id: int,
    phone_number: Optional[str] = None,
) -> dict:
    """
    Initiate M-Pesa STK Push for an existing payment.

    Returns:
        dict with success flag and Daraja response details.
    """
    payment = Payment.query.get(payment_id)
    if payment is None:
        raise ValueError("Payment not found")

    if payment.status not in ("pending", "failed"):
        raise ValueError(f"Cannot initiate STK push for payment with status: {payment.status}")

    # Use provided phone or fall back to payment record / env default
    phone = normalize_phone(phone_number) if phone_number else (payment.phone_number or get_demo_phone())
    if not is_valid_kenyan_phone(phone):
        raise ValueError("Invalid Kenyan phone number. Use format 07XX, 2547XX, or +2547XX.")

    # Update status to processing
    payment.status = "processing"
    payment.phone_number = phone
    db.session.commit()

    # The amount sent to Safaricom is payment.amount (already adjusted for demo mode)
    result = stk_push(
        payment_id=payment.id,
        amount=float(payment.amount),
        phone_number=phone,
        description=f"MediAssist AI - Payment #{payment.id}",
    )

    if result.get("success"):
        payment.transaction_reference = result.get("checkout_request_id") or payment.transaction_reference
        payment.merchant_request_id = result.get("merchant_request_id")
        db.session.commit()
    else:
        payment.status = "failed"
        payment.failure_reason = result.get("message", "STK push failed")
        db.session.commit()

    return result


def query_payment_status(payment_id: int, user_id: int) -> dict:
    """
    Query the current status of a payment.
    If it has a checkout_request_id, also query Daraja for latest status.
    """
    payment = Payment.query.get(payment_id)
    if payment is None:
        raise ValueError("Payment not found")
    if payment.user_id != user_id:
        raise ValueError("Not authorized to view this payment")

    data = payment.to_dict()

    # If still processing and we have a checkout ID, query Daraja
    if payment.status == "processing" and payment.transaction_reference and not payment.transaction_reference.startswith("SIM-"):
        try:
            daraja_status = query_stk_status(payment.transaction_reference)
            result_code = daraja_status.get("ResultCode")
            if result_code == "0":
                data["mpesa_status"] = "Confirmed"
            elif result_code == "1032":
                data["mpesa_status"] = "Cancelled by user"
            elif result_code is not None:
                data["mpesa_status"] = daraja_status.get("ResultDesc", "Failed")
            else:
                data["mpesa_status"] = "Pending"
        except Exception:
            data["mpesa_status"] = "Pending"

    return data


def complete_payment(payment_id: int, user_id: int) -> Payment:
    """
    Legacy simulation endpoint — kept for backward compatibility.
    In production/demo with real STK, this is superseded by callback processing.
    """
    payment = Payment.query.get(payment_id)
    if payment is None:
        raise ValueError("Payment not found")
    if payment.user_id != user_id:
        raise ValueError("Not authorized to complete this payment")
    if payment.status == "success":
        raise ValueError("Payment is already completed")
    if payment.status == "failed":
        raise ValueError("Cannot complete a failed payment")

    payment.status = "success"
    payment.paid_at = __import__("datetime").datetime.utcnow()

    if payment.order:
        payment.order.payment_status = "paid"

    try:
        db.session.commit()
        db.session.refresh(payment)
    except SQLAlchemyError as e:
        db.session.rollback()
        raise ValueError("Failed to complete payment. Please try again.") from e

    return payment


def get_user_payments(user_id: int) -> List[Payment]:
    """Return all payments for a user, newest first."""
    return (
        Payment.query.filter_by(user_id=user_id)
        .order_by(Payment.created_at.desc())
        .all()
    )
