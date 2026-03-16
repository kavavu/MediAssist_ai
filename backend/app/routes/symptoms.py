"""
Symptom prediction API: POST /api/predict (patient only).

Pipeline:
  - Validate symptoms_text presence and minimum length
  - Call prediction_service (which performs spell correction, validation,
    and top-3 prediction using the ML model)
  - Save a SymptomReport row
  - Return a structured response including multiple predictions and a
    human-readable recommendation.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..services.prediction_service import SymptomValidationError, predict_and_save
from ..utils.decorators import role_required

symptoms_bp = Blueprint("symptoms", __name__)


@symptoms_bp.post("/predict")
@jwt_required()
@role_required("patient")
def predict():
    """
    Expects JSON: { "symptoms_text": "fever headache nausea" }.

    Response on success (201):
    {
      "report_id": 14,
      "symptoms": "fever headache nausea",
      "predictions": [
        {"condition": "Malaria", "confidence": 0.72},
        {"condition": "Typhoid", "confidence": 0.18},
        {"condition": "Dengue", "confidence": 0.10}
      ],
      "recommendation": "Consult a doctor or book a lab test"
    }

    Validation errors return 400 with a JSON body: { "message": "<reason>" }.
    """
    data = request.get_json(silent=True) or {}
    symptoms_text = data.get("symptoms_text")
    if symptoms_text is None:
        return jsonify({"message": "Missing symptoms_text"}), 400

    user = get_current_user()
    try:
        report, predictions, low_confidence = predict_and_save(
            user_id=user.id, symptoms_text=symptoms_text
        )
    except SymptomValidationError as exc:
        return jsonify({"message": str(exc)}), 400

    # Confidence-aware recommendation
    if low_confidence:
        recommendation = "The system cannot confidently predict a condition. Please consult a doctor."
    else:
        recommendation = "Consult a doctor or book a lab test"

    return (
        jsonify(
            {
                "report_id": report.id,
                "symptoms": report.symptoms_text,
                "predictions": predictions,
                "recommendation": recommendation,
            }
        ),
        201,
    )
