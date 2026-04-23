"""
Database models (tables): User, PatientProfile, SymptomReport, LabTest, Medicine, Appointment, Order, Consultation, FollowUp.

Imported here so Flask-Migrate and db.create_all() see every table.

NOTE: Consultation must be imported before User because User has relationships
that reference Consultation. FollowUp must be imported before User as well.
"""
from .consultation import Consultation
from .followup import FollowUp
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
    "Consultation",
    "FollowUp",
]
