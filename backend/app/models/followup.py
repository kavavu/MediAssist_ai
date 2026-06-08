"""Follow-up message model for doctor-patient consultation thread."""
from datetime import datetime
from ..extensions import db


class FollowUp(db.Model):
    """A follow-up message in a consultation thread."""
    __tablename__ = "followups"

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(
        db.Integer, db.ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sender_role = db.Column(db.String(16), nullable=False)  # "doctor" or "patient"
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    sender = db.relationship("User", back_populates="followups")

    def to_dict(self):
        return {
            "id": self.id,
            "consultation_id": self.consultation_id,
            "sender_role": self.sender_role,
            "sender_name": self.sender.name if self.sender else None,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
