"""
Patient profile: extended data for users with role 'patient'.
"""
from ..extensions import db


class PatientProfile(db.Model):
    """
    Profile for patient users: age, gender, allergies, chronic conditions.
    """

    __tablename__ = "patient_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(32), nullable=True)
    allergies = db.Column(db.Text, nullable=True)  # free text or JSON later
    chronic_conditions = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="patient_profile")

    def __repr__(self):
        return f"<PatientProfile user_id={self.user_id}>"
