"""
Doctor API (requires JWT + role "doctor"): GET /api/doctor/symptom-reports.
Returns all symptom reports from all patients (for doctor to review).
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..models import SymptomReport
from ..utils.decorators import role_required

doctor_bp = Blueprint("doctor", __name__)


def _symptom_report_payload(r):
    """Serialize a SymptomReport for JSON, including patient info."""
    return {
        "id": r.id,
        "user_id": r.user_id,
        "patient_name": r.user.name if r.user else None,
        "patient_email": r.user.email if r.user else None,
        "symptoms_text": r.symptoms_text,
        "predicted_condition": r.predicted_condition,
        "confidence_score": float(r.confidence_score) if r.confidence_score is not None else None,
        "top_predictions": r.top_predictions or None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@doctor_bp.get("/symptom-reports")
@jwt_required()
@role_required("doctor")
def list_symptom_reports():
    """Return all symptom reports (all patients), newest first."""
    reports = (
        SymptomReport.query
        .order_by(SymptomReport.created_at.desc())
        .all()
    )
    return jsonify({"symptom_reports": [_symptom_report_payload(r) for r in reports]})
