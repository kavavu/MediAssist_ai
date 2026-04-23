"""
Symptom prediction API: POST /api/predict (patient only).

Pipeline:
  - Validate symptoms_text presence and minimum length
  - Call prediction_service (which performs spell correction, validation,
    and top-3 prediction using the ML model)
  - Save a SymptomReport row
  - Return a structured response including multiple predictions and a
    human-readable recommendation.

Error Handling:
  - Returns 400 for invalid input
  - Returns 500 if model is not loaded
  - Returns 503 if prediction service is unavailable
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from ..services.prediction_service import SymptomValidationError, predict_and_save
from ..utils.decorators import role_required
from ..ml.symptom_model import get_model_info

# Setup logging
logger = logging.getLogger(__name__)

symptoms_bp = Blueprint("symptoms", __name__)


@symptoms_bp.post("/predict")
@jwt_required()
@role_required("patient")
def predict():
    """
    Predict disease from symptoms.
    
    Expects JSON: 
    {
        "symptoms": "fever headache cough"
    }
    
    Response on success (201):
    {
        "predicted_condition": "Malaria",
        "confidence": 0.85,
        "report_id": 14,
        "symptoms": "fever headache cough",
        "predictions": [
            {"condition": "Malaria", "confidence": 0.85},
            {"condition": "Typhoid", "confidence": 0.10},
            {"condition": "Dengue", "confidence": 0.05}
        ],
        "recommendation": "Consult a doctor or book a lab test"
    }
    
    Error responses:
    - 400: Missing or invalid symptoms
    - 500: Model not loaded or internal error
    """
    # Log request
    logger.info("Received prediction request")
    
    # Check if model is loaded
    model_info = get_model_info()
    if not model_info.get("loaded"):
        logger.error(f"Model not loaded: {model_info.get('error')}")
        return jsonify({
            "message": "Prediction service unavailable. Model not loaded.",
            "error": model_info.get("error", "Unknown error")
        }), 500
    
    # Parse request body
    data = request.get_json(silent=True) or {}
    
    # Support both "symptoms" and "symptoms_text" for flexibility
    symptoms_text = data.get("symptoms") or data.get("symptoms_text")
    
    if symptoms_text is None:
        logger.warning("Missing symptoms in request")
        return jsonify({"message": "Missing 'symptoms' field"}), 400
    
    if not isinstance(symptoms_text, str):
        logger.warning(f"Invalid symptoms type: {type(symptoms_text)}")
        return jsonify({"message": "Symptoms must be a string"}), 400
    
    symptoms_text = symptoms_text.strip()
    
    if not symptoms_text:
        logger.warning("Empty symptoms text received")
        return jsonify({"message": "Symptoms cannot be empty"}), 400
    
    logger.info(f"Processing symptoms: '{symptoms_text[:100]}...' " if len(symptoms_text) > 100 else f"Processing symptoms: '{symptoms_text}'")
    
    # Get current user
    user = get_current_user()
    if not user:
        logger.error("Could not get current user from JWT")
        return jsonify({"message": "Authentication error"}), 401
    
    try:
        # Make prediction and save report
        report, predictions, low_confidence = predict_and_save(
            user_id=user.id, symptoms_text=symptoms_text
        )
        
        # Get primary prediction
        primary_prediction = predictions[0] if predictions else {"condition": "Unknown", "confidence": 0.0}
        
        # Confidence-aware recommendation
        if low_confidence:
            recommendation = "The system cannot confidently predict a condition. Please consult a doctor."
        else:
            recommendation = "Consult a doctor or book a lab test"
        
        # Log success
        logger.info(f"Prediction successful: {primary_prediction['condition']} (confidence: {primary_prediction['confidence']:.4f})")
        
        # Return response matching expected format
        return jsonify({
            "predicted_condition": primary_prediction["condition"],
            "confidence": primary_prediction["confidence"],
            "report_id": report.id,
            "symptoms": report.symptoms_text,
            "predictions": predictions,
            "recommendation": recommendation,
        }), 201
        
    except SymptomValidationError as exc:
        logger.warning(f"Validation error: {exc}")
        return jsonify({"message": str(exc)}), 400
        
    except Exception as exc:
        logger.error(f"Prediction error: {exc}", exc_info=True)
        return jsonify({
            "message": "Prediction failed due to internal error",
            "error": str(exc)
        }), 500


@symptoms_bp.get("/model-info")
def model_info():
    """
    Get information about the loaded ML model.
    
    Response:
    {
        "loaded": true,
        "accuracy": 0.9762,
        "version": "1.0",
        "num_symptoms": 132
    }
    """
    info = get_model_info()
    return jsonify(info), 200
