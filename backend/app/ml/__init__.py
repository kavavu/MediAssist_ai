"""
Machine learning utilities and model loading.

The basic symptom classification model will live here.
"""

from pathlib import Path

# Base directory for the ML module
ML_DIR = Path(__file__).resolve().parent

# Directories
DATASETS_DIR = ML_DIR / "datasets"
ARTIFACTS_DIR = ML_DIR / "artifacts"

# Dataset paths
TRAINING_DATASET_PATH = DATASETS_DIR / "Training.csv"
TESTING_DATASET_PATH = DATASETS_DIR / "Testing.csv"

# Model artifacts
MODEL_PATH = ARTIFACTS_DIR / "symptom_model.joblib"
VALID_SYMPTOMS_PATH = ARTIFACTS_DIR / "valid_symptoms.json"

__all__ = [
    "ML_DIR",
    "DATASETS_DIR",
    "ARTIFACTS_DIR",
    "TRAINING_DATASET_PATH",
    "TESTING_DATASET_PATH",
    "MODEL_PATH",
    "VALID_SYMPTOMS_PATH",
]
