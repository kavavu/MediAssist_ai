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
    role = db.Column(db.String(32), nullable=False, default="patient", index=True)  # patient | doctor | admin
    specialization = db.Column(db.String(128), nullable=True)
    is_available = db.Column(db.Boolean, default=True, index=True)
    current_load = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    patient_profile = db.relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    symptom_reports = db.relationship(
        "SymptomReport", back_populates="user", foreign_keys="SymptomReport.user_id",
        cascade="all, delete-orphan"
    )
    orders = db.relationship(
        "Order", back_populates="user", foreign_keys="Order.user_id",
        cascade="all, delete-orphan"
    )
    appointments_as_patient = db.relationship(
        "Appointment", back_populates="patient", foreign_keys="Appointment.patient_id",
        cascade="all, delete-orphan"
    )
    appointments_as_doctor = db.relationship(
        "Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id",
        cascade="all, delete-orphan"
    )
    consultations_as_patient = db.relationship(
        "Consultation", back_populates="patient", foreign_keys="Consultation.patient_id",
        cascade="all, delete-orphan"
    )
    consultations_as_doctor = db.relationship(
        "Consultation", back_populates="doctor", foreign_keys="Consultation.doctor_id",
        cascade="all, delete-orphan"
    )
    followups = db.relationship(
        "FollowUp", back_populates="sender", foreign_keys="FollowUp.sender_id",
        cascade="all, delete-orphan"
    )
    payments = db.relationship(
        "Payment", back_populates="user", foreign_keys="Payment.user_id", cascade="all, delete-orphan"
    )
    reviews_given = db.relationship(
        "Review", back_populates="patient", foreign_keys="Review.patient_id", cascade="all, delete-orphan"
    )
    reviews_received = db.relationship(
        "Review", back_populates="doctor", foreign_keys="Review.doctor_id", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"
