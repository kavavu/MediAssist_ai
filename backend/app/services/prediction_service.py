"""
Symptom prediction service.

Responsibilities:
- Clean and validate raw symptom text.
- Call the ML model for predictions (top-3, with confidence and validation).
- Persist a SymptomReport row including the primary prediction and
  top_predictions JSON.
- Return structured data for the API layer to serialize.

Used by the /api/predict route.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..extensions import db
from ..models import SymptomReport
from ..ml.symptom_model import predict_topk


class SymptomValidationError(ValueError):
    """Raised when the symptom input is invalid for prediction."""


def _prepare_input(symptoms_text: str) -> str:
    """Trim whitespace and perform basic length validation."""
    cleaned = (symptoms_text or "").strip()
    if not cleaned:
        raise SymptomValidationError("Symptoms text cannot be empty.")
    if len(cleaned) < 3:
        raise SymptomValidationError("Symptoms text is too short. Please describe your symptoms in more detail.")
    return cleaned


def predict_and_save(user_id: int, symptoms_text: str) -> Tuple[SymptomReport, List[Dict[str, float]], bool]:
    """
    Run the symptom classifier on the given text, save a SymptomReport,
    and return:
      (report, predictions, low_confidence_flag)

    - predictions: list of {"condition": str, "confidence": float}
    - low_confidence_flag: True if the top prediction is below threshold.

    Raises SymptomValidationError when the input is not suitable for prediction
    (empty text, too short, or unrecognized symptoms).
    """
    cleaned = _prepare_input(symptoms_text)

    result = predict_topk(cleaned)
    if "error" in result:
        raise SymptomValidationError(result["error"])

    predictions = result.get("predictions", [])
    low_confidence = bool(result.get("low_confidence", False))

    best_condition = None
    best_confidence = None
    if predictions:
        best_condition = predictions[0]["condition"]
        best_confidence = float(predictions[0]["confidence"])

    # Store top_predictions as a simple mapping {condition: confidence}
    top_predictions_map = {p["condition"]: float(p["confidence"]) for p in predictions}

    report = SymptomReport(
        user_id=user_id,
        symptoms_text=cleaned,
        predicted_condition=best_condition,
        confidence_score=best_confidence,
        top_predictions=top_predictions_map or None,
    )
    db.session.add(report)
    db.session.commit()
    db.session.refresh(report)

    return report, predictions, low_confidence
