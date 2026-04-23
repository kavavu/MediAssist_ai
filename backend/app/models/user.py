"""
User model for authentication and role-based access.
"""
from datetime import datetime

from ..extensions import db


class User(db.Model):
    """
    User account: patients, doctors, and admins.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="patient")  # patient | doctor | admin
    specialization = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    patient_profile = db.relationship("PatientProfile", back_populates="user", uselist=False)
    symptom_reports = db.relationship("SymptomReport", back_populates="user", foreign_keys="SymptomReport.user_id")
    orders = db.relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    appointments_as_patient = db.relationship(
        "Appointment", back_populates="patient", foreign_keys="Appointment.patient_id"
    )
    appointments_as_doctor = db.relationship(
        "Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id"
    )
    consultations_as_patient = db.relationship(
        "Consultation", back_populates="patient", foreign_keys="Consultation.patient_id"
    )
    consultations_as_doctor = db.relationship(
        "Consultation", back_populates="doctor", foreign_keys="Consultation.doctor_id"
    )
    followups = db.relationship(
        "FollowUp", back_populates="sender", foreign_keys="FollowUp.sender_id"
    )

    def __repr__(self):
        return f"<User {self.email}>"
