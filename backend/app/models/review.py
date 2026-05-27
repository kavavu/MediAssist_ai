"""
Review & Rating model for doctor consultations.
Patients can leave one review per resolved consultation.
"""
from datetime import datetime

from ..extensions import db


class Review(db.Model):
    """
    A patient review for a doctor after a resolved consultation.
    Only one review is allowed per consultation.
    """

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consultation_id = db.Column(
        db.Integer, db.ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    patient = db.relationship("User", foreign_keys=[patient_id], back_populates="reviews_given")
    doctor = db.relationship("User", foreign_keys=[doctor_id], back_populates="reviews_received")
    consultation = db.relationship("Consultation", back_populates="review")

    def to_dict(self, include_names=True):
        data = {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "consultation_id": self.consultation_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_names:
            data["patient_name"] = self.patient.name if self.patient else None
            data["doctor_name"] = self.doctor.name if self.doctor else None
        return data

    def __repr__(self):
        return f"<Review id={self.id} consultation={self.consultation_id} rating={self.rating}>"
