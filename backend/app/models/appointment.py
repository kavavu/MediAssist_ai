"""
Appointment: booking between a patient and a doctor.
"""
from ..extensions import db


class Appointment(db.Model):
    """
    An appointment linking a patient (User) and a doctor (User) with datetime and status.
    """

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="scheduled")  # e.g. scheduled, completed, cancelled

    patient = db.relationship("User", back_populates="appointments_as_patient", foreign_keys=[patient_id])
    doctor = db.relationship("User", back_populates="appointments_as_doctor", foreign_keys=[doctor_id])

    def __repr__(self):
        return f"<Appointment id={self.id} patient={self.patient_id} doctor={self.doctor_id}>"
