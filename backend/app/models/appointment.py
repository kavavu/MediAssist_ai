"""
Appointment: booking between a patient and a doctor.
"""
from datetime import datetime

from ..extensions import db


class Appointment(db.Model):
    """
    An appointment linking a patient (User) and a doctor (User) with date, time, status, and optional consultation link.
    """

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consultation_id = db.Column(
        db.Integer, db.ForeignKey("consultations.id", ondelete="SET NULL"), nullable=True
    )
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="scheduled")  # scheduled | completed | cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    patient = db.relationship("User", back_populates="appointments_as_patient", foreign_keys=[patient_id])
    doctor = db.relationship("User", back_populates="appointments_as_doctor", foreign_keys=[doctor_id])
    consultation = db.relationship("Consultation", back_populates="appointments")

    def to_dict(self, include_names=True):
        data = {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "consultation_id": self.consultation_id,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "appointment_time": self.appointment_time,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_names:
            data["patient_name"] = self.patient.name if self.patient else None
            data["doctor_name"] = self.doctor.name if self.doctor else None
        return data

    def __repr__(self):
        return f"<Appointment id={self.id} patient={self.patient_id} doctor={self.doctor_id} date={self.appointment_date} time={self.appointment_time}>"
