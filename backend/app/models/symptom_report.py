"""
Symptom report: user-submitted symptoms and AI prediction result.
"""
from datetime import datetime

from ..extensions import db


class SymptomReport(db.Model):
    """
    A single symptom submission with predicted condition and confidence.
    """

    __tablename__ = "symptom_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symptoms_text = db.Column(db.Text, nullable=False)
    predicted_condition = db.Column(db.String(255), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    # JSON mapping of condition → confidence, e.g. {"Malaria": 0.72, "Typhoid": 0.18}
    top_predictions = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="symptom_reports")

    def __repr__(self):
        return f"<SymptomReport id={self.id} user_id={self.user_id}>"
