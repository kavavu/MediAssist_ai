"""
Symptom classification model for MediAssist AI.

This module is now a THIN WRAPPER around the Hybrid Clinical Prediction Engine
(backend/app/ml/clinical/engine.py). The clinical engine uses rule-based weighted
symptom scoring as the PRIMARY predictor, with the old RandomForest model available
as an optional fallback for edge cases.

The old ML model loading, prediction, red-flag detection, confidence calibration,
and condition weighting have been superseded by the clinical engine.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Directory for persisted model
_ML_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_ML_DIR, "artifacts", "symptom_model.joblib")
_VALID_SYMPTOMS_PATH = os.path.join(_ML_DIR, "artifacts", "valid_symptoms.json")

# Cached state
_model_data: Optional[Dict] = None
_valid_symptoms: Optional[List[str]] = None


def load_model() -> Dict:
    """
    Load the trained model and metadata from disk.
    Kept for backward compatibility and ML fallback.
    """
    global _model_data

    if _model_data is not None:
        return _model_data

    if not os.path.isfile(_MODEL_PATH):
        logger.error(f"Model file not found: {_MODEL_PATH}")
        raise FileNotFoundError(
            f"Model file not found. Please run training first: {_MODEL_PATH}"
        )

    try:
        _model_data = joblib.load(_MODEL_PATH)
        logger.info(f"ML model loaded successfully. Accuracy: {_model_data.get('accuracy', 'N/A')}")
        return _model_data
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def load_valid_symptoms() -> List[str]:
    """Load the list of valid symptom names. Kept for backward compatibility."""
    global _valid_symptoms

    if _valid_symptoms is not None:
        return _valid_symptoms

    if os.path.isfile(_VALID_SYMPTOMS_PATH):
        try:
            with open(_VALID_SYMPTOMS_PATH, "r", encoding="utf-8") as f:
                _valid_symptoms = json.load(f)
            logger.info(f"Loaded {len(_valid_symptoms)} valid symptoms")
            return _valid_symptoms
        except Exception as e:
            logger.warning(f"Failed to load valid symptoms: {e}")

    # Fallback: extract from model data
    try:
        model_data = load_model()
        _valid_symptoms = model_data.get("symptom_names", [])
        return _valid_symptoms
    except:
        logger.error("Could not load valid symptoms list")
        return []


def predict(symptoms_text: str) -> Tuple[Optional[str], float]:
    """
    Predict disease from symptoms text.
    Delegates to the clinical engine for the primary prediction.

    Returns:
        Tuple of (predicted_condition, confidence_score)
        Returns (None, 0.0) if prediction fails
    """
    logger.info(f"Prediction request (wrapper): '{symptoms_text}'")

    if not symptoms_text or not symptoms_text.strip():
        logger.warning("Empty symptoms text received")
        return None, 0.0

    try:
        from .clinical.engine import predict_topk
        result = predict_topk(symptoms_text, k=1, use_ml_fallback=False)

        if result.get("error"):
            logger.warning(f"Clinical engine error: {result['error']}")
            return None, 0.0

        predictions = result.get("top_3_predictions", [])
        if predictions:
            return predictions[0]["condition"], predictions[0]["confidence"]
        return None, 0.0

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return None, 0.0


def predict_topk(
    symptoms_text: str,
    k: int = 3,
    confidence_threshold: float = 0.30
) -> Dict:
    """
    Predict top-k diseases from symptoms with confidence scores.

    PRIMARY: Delegates to the Hybrid Clinical Prediction Engine.
    The clinical engine uses rule-based weighted symptom scoring focused on
    tropical diseases relevant to Kenya/East Africa.

    Args:
        symptoms_text: String of symptoms
        k: Number of top predictions to return
        confidence_threshold: Minimum confidence for "low_confidence" flag

    Returns:
        Dictionary with backward-compatible keys plus new clinical fields:
        - cleaned_text: Normalized symptom string
        - predictions: List of {condition, confidence} dicts
        - low_confidence: Boolean
        - red_flag: Boolean
        - detected_red_flags: List of detected emergency symptoms
        - match_quality: String label ("High Match", "Moderate Match", "Low Match")
        - severity: str (LOW, MEDIUM, HIGH)
        - urgency_message: str
        - recommended_tests: list of str
        - clinical_insight: str
        - ai_advice: str
    """
    logger.info(f"Top-k prediction request (wrapper): '{symptoms_text}'")

    try:
        from .clinical.engine import predict_topk as clinical_predict_topk
        result = clinical_predict_topk(symptoms_text, k=k, confidence_threshold=confidence_threshold)

        # Map clinical engine response to backward-compatible format
        # plus new fields
        return {
            "cleaned_text": ", ".join(result.get("cleaned_symptoms", [])),
            "predictions": result.get("top_3_predictions", []),
            "low_confidence": result.get("low_confidence", True),
            "red_flag": result.get("red_flag", False),
            "detected_red_flags": result.get("detected_red_flags", []),
            "match_quality": result.get("match_quality", "Low Match"),
            "severity": result.get("severity", "LOW"),
            "urgency_message": result.get("urgency_message", ""),
            "recommended_tests": result.get("recommended_tests", []),
            "clinical_insight": result.get("clinical_insight", ""),
            "ai_advice": result.get("ai_advice", ""),
            "error": result.get("error"),
        }

    except Exception as e:
        logger.error(f"Top-k prediction error: {e}")
        return {
            "error": f"Prediction failed: {str(e)}"
        }


def get_model_info() -> Dict:
    """
    Get information about the prediction engine.
    Returns clinical engine info; ML model info is secondary.
    """
    try:
        from .clinical.engine import get_model_info as clinical_info
        info = clinical_info()
        # Also include ML model info if available
        try:
            ml_data = load_model()
            info["ml_model"] = {
                "loaded": True,
                "accuracy": ml_data.get("accuracy", "N/A"),
                "version": ml_data.get("version", "N/A"),
                "num_symptoms": len(ml_data.get("symptom_names", [])),
            }
        except Exception:
            info["ml_model"] = {"loaded": False}
        return info
    except Exception as e:
        return {
            "loaded": False,
            "error": str(e)
        }
