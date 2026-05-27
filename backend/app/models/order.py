"""
Order: user order for a lab test or medicine.
"""
from datetime import datetime

from ..extensions import db


class Order(db.Model):
    """
    An order placed by a user for either a lab_test or a medicine (item_type + item_id).
    """

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_type = db.Column(db.String(32), nullable=False)  # 'lab_test' | 'medicine'
    item_id = db.Column(db.Integer, nullable=False)  # FK to lab_tests.id or medicines.id
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.String(32), nullable=False, default="pending")  # e.g. pending, paid
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders")
    payment = db.relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order id={self.id} user_id={self.user_id} {self.item_type}={self.item_id}>"
