"""
Payment business logic (demo/simulation — no real M-Pesa integration).

- Create payment records
- Simulate completion
- Fetch user payment history

SAFETY: All DB operations use explicit transaction blocks with rollback on failure.
"""
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Payment, User, Appointment, Order

_PAYMENT_METHODS = {"M-Pesa", "Card", "Cash"}


def create_payment(
    user_id: int,
    amount: float,
    payment_method: str = "M-Pesa",
    appointment_id: Optional[int] = None,
    order_id: Optional[int] = None,
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
        # Check for existing completed payment on this appointment
        existing = Payment.query.filter_by(
            appointment_id=appointment_id, status="completed"
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
            order_id=order_id, status="completed"
        ).first()
        if existing:
            raise ValueError("This order has already been paid for")

    payment = Payment(
        user_id=user_id,
        appointment_id=appointment_id,
        order_id=order_id,
        amount=Decimal(str(amount)),
        payment_method=payment_method,
        transaction_reference=f"SIM-{uuid.uuid4().hex[:12].upper()}",
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


def complete_payment(payment_id: int, user_id: int) -> Payment:
    """
    Simulate completing a payment (demo only).
    Raises ValueError if not found, not owned, or already completed/failed.

    SAFETY: Uses a single transaction block to update payment and linked order atomically.
    """
    payment = Payment.query.get(payment_id)
    if payment is None:
        raise ValueError("Payment not found")
    if payment.user_id != user_id:
        raise ValueError("Not authorized to complete this payment")
    if payment.status == "completed":
        raise ValueError("Payment is already completed")
    if payment.status == "failed":
        raise ValueError("Cannot complete a failed payment")

    payment.status = "completed"

    # Update linked order payment_status if applicable — within SAME transaction
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
