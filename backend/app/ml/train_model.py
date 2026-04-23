"""
Training script for the symptom classifier using Training.csv and Testing.csv datasets.

Dataset format:
- Binary encoded symptoms (0/1) where each column is a symptom
- Last column is the target label (disease/condition)

Usage:
    cd backend
    python -m app.ml.train_model

Output:
- symptom_model.joblib: Trained model pipeline
- valid_symptoms.json: List of valid symptom names
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import StandardScaler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
ML_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ML_DIR / "artifacts"
DATASETS_DIR = ML_DIR / "datasets"
MODEL_PATH = ARTIFACTS_DIR / "symptom_model.joblib"
VALID_SYMPTOMS_PATH = ARTIFACTS_DIR / "valid_symptoms.json"


def load_dataset(csv_path: Path) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Load a CSV dataset with binary-encoded symptoms.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        X: Feature DataFrame (symptom columns)
        y: Target Series (disease labels)
        symptom_names: List of symptom column names
    """
    logger.info(f"Loading dataset from: {csv_path}")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Find the target column ('prognosis')
    if 'prognosis' not in df.columns:
        raise ValueError("Dataset must contain a 'prognosis' column")
    
    # Get all symptom columns (exclude 'prognosis' and any unnamed columns)
    symptom_cols = [c for c in df.columns if c not in ['prognosis'] and not c.startswith('Unnamed:')]
    
    logger.info(f"Target column: prognosis")
    logger.info(f"Number of symptoms: {len(symptom_cols)}")
    
    # Extract features and target
    X = df[symptom_cols].fillna(0).astype(int)
    y = df['prognosis'].fillna("Unknown")
    
    # Clean symptom names (remove underscores, extra spaces)
    clean_symptom_names = [s.replace("_", " ").strip() for s in symptom_cols]
    X.columns = clean_symptom_names
    
    # Remove rows with missing targets
    valid_mask = y != "Unknown"
    X = X[valid_mask]
    y = y[valid_mask]
    
    logger.info(f"Final dataset: {len(X)} samples, {len(clean_symptom_names)} features")
    logger.info(f"Number of unique diseases: {y.nunique()}")
    
    return X, y, clean_symptom_names


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_type: str = "random_forest"
) -> Tuple[object, float]:
    """
    Train a classification model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Testing features
        y_test: Testing labels
        model_type: Type of model ('random_forest', 'logistic_regression', 'naive_bayes')
        
    Returns:
        model: Trained model
        accuracy: Test accuracy
    """
    logger.info(f"Training {model_type} model...")
    
    if model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            n_jobs=-1
        )
    elif model_type == "logistic_regression":
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            n_jobs=-1
        )
    elif model_type == "naive_bayes":
        model = MultinomialNB()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Train
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred, zero_division=0))
    
    return model, accuracy


def save_artifacts(
    model: object,
    symptom_names: List[str],
    accuracy: float
) -> None:
    """
    Save model and symptom list to artifacts directory.
    
    Args:
        model: Trained model
        symptom_names: List of valid symptom names
        accuracy: Model accuracy
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model with metadata
    model_data = {
        "model": model,
        "symptom_names": symptom_names,
        "accuracy": accuracy,
        "version": "1.0"
    }
    
    joblib.dump(model_data, MODEL_PATH)
    logger.info(f"Model saved to: {MODEL_PATH}")
    
    # Save valid symptoms list
    with open(VALID_SYMPTOMS_PATH, "w", encoding="utf-8") as f:
        json.dump(symptom_names, f, ensure_ascii=False, indent=2)
    logger.info(f"Valid symptoms list saved to: {VALID_SYMPTOMS_PATH}")


def main() -> None:
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("MediAssist AI - Symptom Model Training")
    logger.info("=" * 60)
    
    # Load datasets
    train_path = DATASETS_DIR / "Training.csv"
    test_path = DATASETS_DIR / "Testing.csv"
    
    try:
        X_train, y_train, symptom_names = load_dataset(train_path)
        X_test, y_test, _ = load_dataset(test_path)
        
        # Ensure test set has same columns as train
        for col in symptom_names:
            if col not in X_test.columns:
                X_test[col] = 0
        X_test = X_test[symptom_names]
        
        # Train model
        model, accuracy = train_model(
            X_train, y_train, X_test, y_test,
            model_type="random_forest"
        )
        
        # Save artifacts
        save_artifacts(model, symptom_names, accuracy)
        
        logger.info("=" * 60)
        logger.info("Training completed successfully!")
        logger.info(f"Final accuracy: {accuracy:.4f}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
