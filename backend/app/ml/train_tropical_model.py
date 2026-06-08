"""
Train a RandomForest classifier on the tropical disease dataset.

This model learns the same 15 diseases as the clinical engine,
allowing the ML fallback to actually contribute meaningful predictions.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

ML_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ML_DIR / "artifacts"
DATASETS_DIR = ML_DIR / "datasets"
MODEL_PATH = ARTIFACTS_DIR / "symptom_model_tropical.joblib"
VALID_SYMPTOMS_PATH = ARTIFACTS_DIR / "valid_symptoms_tropical.json"


def load_dataset(csv_path: Path) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Load a CSV dataset with binary-encoded symptoms."""
    logger.info(f"Loading dataset from: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    if "prognosis" not in df.columns:
        raise ValueError("Dataset must contain a 'prognosis' column")

    symptom_cols = [c for c in df.columns if c != "prognosis" and not c.startswith("Unnamed:")]

    X = df[symptom_cols].fillna(0).astype(int)
    y = df["prognosis"].fillna("Unknown")

    clean_names = [s.replace("_", " ").strip() for s in symptom_cols]
    X.columns = clean_names

    valid_mask = y != "Unknown"
    X = X[valid_mask]
    y = y[valid_mask]

    logger.info(f"Final dataset: {len(X)} samples, {len(clean_names)} features")
    logger.info(f"Number of unique diseases: {y.nunique()}")

    return X, y, clean_names


def train_model(X_train, y_train, X_test, y_test):
    """Train and evaluate a RandomForest classifier."""
    logger.info("Training RandomForest model...")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=25,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred, zero_division=0))

    return model, accuracy


def save_artifacts(model, symptom_names, accuracy):
    """Save model and metadata."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    model_data = {
        "model": model,
        "symptom_names": symptom_names,
        "accuracy": accuracy,
        "version": "2.0-tropical",
        "diseases": list(model.classes_),
    }

    joblib.dump(model_data, MODEL_PATH)
    logger.info(f"Model saved to: {MODEL_PATH}")

    with open(VALID_SYMPTOMS_PATH, "w", encoding="utf-8") as f:
        json.dump(symptom_names, f, ensure_ascii=False, indent=2)
    logger.info(f"Valid symptoms saved to: {VALID_SYMPTOMS_PATH}")


def main():
    logger.info("=" * 60)
    logger.info("MediAssist AI - Tropical Disease Model Training")
    logger.info("=" * 60)

    train_path = DATASETS_DIR / "Training_Tropical.csv"
    test_path = DATASETS_DIR / "Testing_Tropical.csv"

    try:
        X_train, y_train, symptom_names = load_dataset(train_path)
        X_test, y_test, _ = load_dataset(test_path)

        # Align columns
        for col in symptom_names:
            if col not in X_test.columns:
                X_test[col] = 0
        X_test = X_test[symptom_names]

        model, accuracy = train_model(X_train, y_train, X_test, y_test)
        save_artifacts(model, symptom_names, accuracy)

        logger.info("=" * 60)
        logger.info(f"Training complete! Accuracy: {accuracy:.4f}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
