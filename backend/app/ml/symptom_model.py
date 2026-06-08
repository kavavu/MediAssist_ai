"""
Symptom classification model for MediAssist AI.

This module provides the ML fallback for the Hybrid Clinical Prediction Engine.
It loads a RandomForest model trained on 15 tropical diseases relevant to Kenya/East Africa.

The clinical engine (backend/app/ml/clinical/engine.py) is the PRIMARY predictor.
This ML model serves as a supporting fallback for edge cases.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# Directory for persisted model
_ML_DIR = os.path.dirname(os.path.abspath(__file__))

# NEW tropical disease model (15 diseases, 65 symptoms)
_TROPICAL_MODEL_PATH = os.path.join(_ML_DIR, "artifacts", "symptom_model_tropical.joblib")
_TROPICAL_SYMPTOMS_PATH = os.path.join(_ML_DIR, "artifacts", "valid_symptoms_tropical.json")

# OLD generic model (41 diseases, 132 symptoms) - kept as ultimate fallback
_MODEL_PATH = os.path.join(_ML_DIR, "artifacts", "symptom_model.joblib")
_VALID_SYMPTOMS_PATH = os.path.join(_ML_DIR, "artifacts", "valid_symptoms.json")

# Cached state
_tropical_model_data: Optional[Dict] = None
_tropical_symptoms: Optional[List[str]] = None
_model_data: Optional[Dict] = None
_valid_symptoms: Optional[List[str]] = None


def _load_tropical_model() -> Dict:
    """Load the tropical disease RandomForest model."""
    global _tropical_model_data

    if _tropical_model_data is not None:
        return _tropical_model_data

    if not os.path.isfile(_TROPICAL_MODEL_PATH):
        logger.warning(f"Tropical model not found: {_TROPICAL_MODEL_PATH}")
        return {}

    try:
        _tropical_model_data = joblib.load(_TROPICAL_MODEL_PATH)
        logger.info(
            f"Tropical ML model loaded. Accuracy: {_tropical_model_data.get('accuracy', 'N/A')}, "
            f"Diseases: {len(_tropical_model_data.get('diseases', []))}"
        )
        return _tropical_model_data
    except Exception as e:
        logger.error(f"Failed to load tropical model: {e}")
        return {}


def _load_tropical_symptoms() -> List[str]:
    """Load the list of valid symptom names for tropical model."""
    global _tropical_symptoms

    if _tropical_symptoms is not None:
        return _tropical_symptoms

    if os.path.isfile(_TROPICAL_SYMPTOMS_PATH):
        try:
            with open(_TROPICAL_SYMPTOMS_PATH, "r", encoding="utf-8") as f:
                _tropical_symptoms = json.load(f)
            return _tropical_symptoms
        except Exception as e:
            logger.warning(f"Failed to load tropical symptoms: {e}")

    # Fallback: extract from model
    try:
        model_data = _load_tropical_model()
        _tropical_symptoms = model_data.get("symptom_names", [])
        return _tropical_symptoms
    except:
        return []


def load_model() -> Dict:
    """Load the trained model and metadata from disk."""
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
    """Load the list of valid symptom names."""
    global _valid_symptoms

    if _valid_symptoms is not None:
        return _valid_symptoms

    if os.path.isfile(_VALID_SYMPTOMS_PATH):
        try:
            with open(_VALID_SYMPTOMS_PATH, "r", encoding="utf-8") as f:
                _valid_symptoms = json.load(f)
            return _valid_symptoms
        except Exception as e:
            logger.warning(f"Failed to load valid symptoms: {e}")

    try:
        model_data = load_model()
        _valid_symptoms = model_data.get("symptom_names", [])
        return _valid_symptoms
    except:
        return []


def _symptoms_to_features(symptoms: List[str], feature_names: List[str]) -> np.ndarray:
    """Convert a list of canonical symptoms to a binary feature vector."""
    features = np.zeros(len(feature_names))
    symptom_set = set(s.lower().replace(" ", "_").replace("-", "_") for s in symptoms)

    for i, feat in enumerate(feature_names):
        feat_normalized = feat.lower().replace(" ", "_").replace("-", "_")
        if feat_normalized in symptom_set:
            features[i] = 1

    return features


def predict(symptoms_text: str) -> Tuple[Optional[str], float]:
    """Predict disease from symptoms text using the clinical engine."""
    logger.info(f"Prediction request (wrapper): '{symptoms_text}'")

    if not symptoms_text or not symptoms_text.strip():
        return None, 0.0

    try:
        from .clinical.engine import predict_topk
        result = predict_topk(symptoms_text, k=1, use_ml_fallback=False)

        if result.get("error"):
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
    FALLBACK: Uses the tropical RandomForest model when clinical confidence is low.
    """
    logger.info(f"Top-k prediction request (wrapper): '{symptoms_text}'")

    try:
        from .clinical.engine import predict_topk as clinical_predict_topk
        result = clinical_predict_topk(symptoms_text, k=k, confidence_threshold=confidence_threshold)

        # Map clinical engine response to backward-compatible format
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


def ml_predict(symptoms: List[str]) -> List[Dict]:
    """
    Use the tropical ML model to predict from a list of canonical symptoms.
    Returns top-3 predictions with confidence scores.
    """
    model_data = _load_tropical_model()
    if not model_data:
        return []

    model = model_data.get("model")
    feature_names = model_data.get("symptom_names", [])
    classes = model_data.get("diseases", [])

    if not model or not feature_names:
        return []

    features = _symptoms_to_features(symptoms, feature_names)

    try:
        # Use DataFrame with feature names to avoid sklearn warning
        import pandas as pd
        feature_df = pd.DataFrame([features], columns=feature_names)
        proba = model.predict_proba(feature_df)[0]
        top_indices = np.argsort(proba)[::-1][:3]

        predictions = []
        for idx in top_indices:
            predictions.append({
                "condition": classes[idx],
                "confidence": round(float(proba[idx]), 4)
            })
        return predictions
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return []


def get_model_info() -> Dict:
    """Get information about the prediction engine."""
    info = {
        "loaded": True,
        "engine": "Hybrid Clinical Prediction Engine",
        "version": "2.0",
        "num_diseases": 15,
        "num_symptoms": 65,
        "primary_method": "Rule-based weighted symptom scoring",
        "fallback_method": "RandomForest (tropical diseases)",
    }

    # Add tropical model info
    try:
        tropical_data = _load_tropical_model()
        info["tropical_ml_model"] = {
            "loaded": True,
            "accuracy": tropical_data.get("accuracy", "N/A"),
            "version": tropical_data.get("version", "N/A"),
            "num_symptoms": len(tropical_data.get("symptom_names", [])),
            "num_diseases": len(tropical_data.get("diseases", [])),
        }
    except:
        info["tropical_ml_model"] = {"loaded": False}

    # Add old model info
    try:
        old_data = load_model()
        info["ml_model"] = {
            "loaded": True,
            "accuracy": old_data.get("accuracy", "N/A"),
            "version": old_data.get("version", "N/A"),
            "num_symptoms": len(old_data.get("symptom_names", [])),
        }
    except:
        info["ml_model"] = {"loaded": False}

    return info
