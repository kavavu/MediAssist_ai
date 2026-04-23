"""
Symptom classification model for MediAssist AI.

This module handles:
- Loading the trained ML model
- Processing symptom input (text to binary vector)
- Making predictions with confidence scores
- Spell correction and validation
"""

from __future__ import annotations

import json
import logging
import os
from difflib import get_close_matches
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
    
    Returns:
        Dictionary containing:
        - 'model': Trained sklearn model
        - 'symptom_names': List of symptom feature names
        - 'accuracy': Model accuracy score
        - 'version': Model version
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
        logger.info(f"Model loaded successfully. Accuracy: {_model_data.get('accuracy', 'N/A')}")
        return _model_data
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def load_valid_symptoms() -> List[str]:
    """
    Load the list of valid symptom names.
    
    Returns:
        List of symptom names that the model recognizes
    """
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


def _tokenize(symptoms_text: str) -> List[str]:
    """
    Tokenize symptoms text into individual symptoms.
    
    Args:
        symptoms_text: Raw symptoms text (comma or space separated)
        
    Returns:
        List of symptom tokens
    """
    if not symptoms_text:
        return []
    
    # Replace commas with spaces, then split
    text = symptoms_text.replace(",", " ").replace("_", " ")
    tokens = [t.strip().lower() for t in text.split()]
    return [t for t in tokens if t]


def _correct_symptoms(
    symptoms: List[str],
    valid_symptoms: List[str],
    cutoff: float = 0.6
) -> List[str]:
    """
    Apply spell correction to symptoms using fuzzy matching.
    
    Args:
        symptoms: List of input symptoms
        valid_symptoms: List of valid symptom names
        cutoff: Minimum similarity score (0-1)
        
    Returns:
        List of corrected symptoms
    """
    corrected = []
    valid_lower = {v.lower(): v for v in valid_symptoms}
    
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        
        # Exact match
        if symptom_lower in valid_lower:
            corrected.append(valid_lower[symptom_lower])
            continue
        
        # Try fuzzy matching
        matches = get_close_matches(
            symptom_lower,
            valid_lower.keys(),
            n=1,
            cutoff=cutoff
        )
        
        if matches:
            corrected.append(valid_lower[matches[0]])
            logger.debug(f"Corrected '{symptom}' -> '{valid_lower[matches[0]]}'")
        else:
            # Keep original if no match found
            corrected.append(symptom)
    
    return corrected


def _symptoms_to_vector(
    symptoms: List[str],
    symptom_names: List[str]
) -> pd.DataFrame:
    """
    Convert list of symptoms to binary feature vector.
    
    Args:
        symptoms: List of symptom names
        symptom_names: List of all possible symptom features
        
    Returns:
        DataFrame with binary features (1 if symptom present, 0 otherwise)
    """
    # Create binary vector
    symptom_set = set(s.lower() for s in symptoms)
    vector = [1 if name.lower() in symptom_set else 0 for name in symptom_names]
    
    # Convert to DataFrame with proper column names
    return pd.DataFrame([vector], columns=symptom_names)


def predict(symptoms_text: str) -> Tuple[Optional[str], float]:
    """
    Predict disease from symptoms text.
    
    Args:
        symptoms_text: String of symptoms (e.g., "fever headache cough")
        
    Returns:
        Tuple of (predicted_condition, confidence_score)
        Returns (None, 0.0) if prediction fails
    """
    logger.info(f"Prediction request: '{symptoms_text}'")
    
    if not symptoms_text or not symptoms_text.strip():
        logger.warning("Empty symptoms text received")
        return None, 0.0
    
    try:
        # Load model
        model_data = load_model()
        model = model_data["model"]
        symptom_names = model_data["symptom_names"]
        
        # Tokenize and correct symptoms
        tokens = _tokenize(symptoms_text)
        logger.info(f"Tokens: {tokens}")
        
        if not tokens:
            logger.warning("No valid symptom tokens found")
            return None, 0.0
        
        valid_symptoms = load_valid_symptoms()
        corrected = _correct_symptoms(tokens, valid_symptoms)
        logger.info(f"Corrected symptoms: {corrected}")
        
        # Convert to feature vector
        X = _symptoms_to_vector(corrected, symptom_names)
        
        # Predict
        prediction = model.predict(X)[0]
        
        # Get confidence (probability)
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            confidence = float(proba.max())
        else:
            confidence = 0.8  # Default confidence if not available
        
        logger.info(f"Prediction: {prediction}, Confidence: {confidence:.4f}")
        
        return prediction, confidence
        
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
    
    Args:
        symptoms_text: String of symptoms
        k: Number of top predictions to return
        confidence_threshold: Minimum confidence for "low_confidence" flag
        
    Returns:
        Dictionary with:
        - cleaned_text: Normalized symptom string
        - predictions: List of {condition, confidence} dicts
        - low_confidence: Boolean indicating if top prediction is below threshold
    """
    logger.info(f"Top-k prediction request: '{symptoms_text}'")
    
    if not symptoms_text or not symptoms_text.strip():
        return {
            "cleaned_text": "",
            "predictions": [],
            "low_confidence": True
        }
    
    try:
        # Load model
        model_data = load_model()
        model = model_data["model"]
        symptom_names = model_data["symptom_names"]
        
        # Tokenize and correct
        tokens = _tokenize(symptoms_text)
        valid_symptoms = load_valid_symptoms()
        corrected = _correct_symptoms(tokens, valid_symptoms)
        
        if not corrected:
            return {
                "error": "No valid symptoms recognized. Please enter valid medical symptoms."
            }
        
        cleaned_text = ", ".join(corrected)
        
        # Convert to vector
        X = _symptoms_to_vector(corrected, symptom_names)
        
        # Get predictions
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            classes = model.classes_
            
            # Sort by probability
            scored = sorted(
                [{"condition": cls, "confidence": float(p)} 
                 for cls, p in zip(classes, proba)],
                key=lambda x: x["confidence"],
                reverse=True
            )
            
            top = scored[:max(1, k)]
            top_conf = top[0]["confidence"] if top else 0.0
            
            return {
                "cleaned_text": cleaned_text,
                "predictions": top,
                "low_confidence": top_conf < confidence_threshold
            }
        else:
            # Fallback for models without predict_proba
            pred = model.predict(X)[0]
            return {
                "cleaned_text": cleaned_text,
                "predictions": [{"condition": pred, "confidence": 0.8}],
                "low_confidence": False
            }
            
    except Exception as e:
        logger.error(f"Top-k prediction error: {e}")
        return {
            "error": f"Prediction failed: {str(e)}"
        }


def get_model_info() -> Dict:
    """
    Get information about the loaded model.
    
    Returns:
        Dictionary with model metadata
    """
    try:
        model_data = load_model()
        return {
            "loaded": True,
            "accuracy": model_data.get("accuracy", "N/A"),
            "version": model_data.get("version", "N/A"),
            "num_symptoms": len(model_data.get("symptom_names", [])),
            "model_path": _MODEL_PATH
        }
    except Exception as e:
        return {
            "loaded": False,
            "error": str(e)
        }
