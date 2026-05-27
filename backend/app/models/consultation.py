"""
Consultation model for doctor-patient telemedicine workflow.
"""
from datetime import datetime
from ..extensions import db


class Consultation(db.Model):
    """A consultation request from patient to doctor."""
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    symptoms = db.Column(db.Text, nullable=False)
    symptoms_clean = db.Column(db.Text, nullable=True)
    predicted_condition = db.Column(db.String(255), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    message = db.Column(db.Text, nullable=True)

    # Structured doctor response fields
    doctor_response = db.Column(db.Text, nullable=True)
    response_acknowledgement = db.Column(db.Text, nullable=True)
    response_advice = db.Column(db.Text, nullable=True)
    response_tests = db.Column(db.Text, nullable=True)
    response_urgency = db.Column(db.Text, nullable=True)

    # AI-generated insight
    ai_insight = db.Column(db.Text, nullable=True)
    ai_risk_level = db.Column(db.String(32), nullable=True)
    ai_suggested_steps = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), nullable=False, default="pending")
    priority = db.Column(db.String(32), nullable=False, default="LOW")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    patient = db.relationship("User", foreign_keys=[patient_id], back_populates="consultations_as_patient")
    doctor = db.relationship("User", foreign_keys=[doctor_id], back_populates="consultations_as_doctor")
    followups = db.relationship("FollowUp", backref="consultation", cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", back_populates="consultation")
    review = db.relationship("Review", back_populates="consultation", uselist=False, cascade="all, delete-orphan")
    files = db.relationship("FileAttachment", back_populates="consultation", cascade="all, delete-orphan")

    def to_dict(self, include_response=True):
        data = {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "symptoms": self.symptoms,
            "symptoms_clean": self.symptoms_clean,
            "predicted_condition": self.predicted_condition,
            "confidence_score": self.confidence_score,
            "message": self.message,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "patient_name": self.patient.name if self.patient else None,
            "patient_email": self.patient.email if self.patient else None,
            "doctor_name": self.doctor.name if self.doctor else None,
            "doctor_specialization": getattr(self.doctor, "specialization", None),
            "doctor_is_available": getattr(self.doctor, "is_available", None),
            "doctor_current_load": getattr(self.doctor, "current_load", None),
            "doctor_is_verified": getattr(self.doctor, "is_verified", None),
            "has_review": self.review is not None,
            "ai_insight": self.ai_insight,
            "ai_risk_level": self.ai_risk_level,
            "ai_suggested_steps": self.ai_suggested_steps,
        }
        if include_response:
            data["doctor_response"] = self.doctor_response
            data["response_acknowledgement"] = self.response_acknowledgement
            data["response_advice"] = self.response_advice
            data["response_tests"] = self.response_tests
            data["response_urgency"] = self.response_urgency
        return data
