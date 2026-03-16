"""
Database models (tables): User, PatientProfile, SymptomReport, LabTest, Medicine, Appointment, Order.

Imported here so Flask-Migrate and db.create_all() see every table.
"""
from .user import User
from .patient_profile import PatientProfile
from .symptom_report import SymptomReport
from .lab_test import LabTest
from .medicine import Medicine
from .appointment import Appointment
from .order import Order

__all__ = [
    "User",
    "PatientProfile",
    "SymptomReport",
    "LabTest",
    "Medicine",
    "Appointment",
    "Order",
]
