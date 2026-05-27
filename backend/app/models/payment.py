"""
Payment model for mock/demo payment processing.
Links to appointments, orders, or standalone transactions.
"""
from datetime import datetime

from ..extensions import db


class Payment(db.Model):
    """
    A payment record for appointments, lab tests, or medicine orders.
    This is a DEMO/SIMULATION system — no real M-Pesa integration.
    """

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Link to either an appointment or an order (nullable = standalone)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(32), nullable=False, default="M-Pesa")  # M-Pesa | Card | Cash
    transaction_reference = db.Column(db.String(128), nullable=True, unique=True)
    status = db.Column(db.String(32), nullable=False, default="pending")  # pending | completed | failed

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="payments")
    appointment = db.relationship("Appointment", back_populates="payment")
    order = db.relationship("Order", back_populates="payment")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "appointment_id": self.appointment_id,
            "order_id": self.order_id,
            "amount": float(self.amount) if self.amount is not None else 0,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Payment id={self.id} user={self.user_id} amount={self.amount} status={self.status}>"
