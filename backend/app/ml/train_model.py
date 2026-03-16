"""
Training script for the symptom classifier using a real medical dataset.

This script is **not** run automatically. You will run it manually once you
have added a CSV dataset under `backend/app/ml/datasets/`.

Expected dataset schema (wide format):
    symptom_1, symptom_2, ... symptom_17, prognosis

Each `symptom_i` cell should contain the name of a symptom for that case
or be empty/NaN. `prognosis` is the target label (diagnosis/condition).

The script will:
  - Load the CSV
  - Combine all symptom_* columns into a single text field
  - Train a TF-IDF + MultinomialNB pipeline
  - Evaluate on a held-out test set and print accuracy
  - Save the trained model to:
        backend/app/ml/artifacts/symptom_model.joblib
  - Save the list of valid symptoms to:
        backend/app/ml/artifacts/valid_symptoms.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Tuple

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


ML_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ML_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "symptom_model.joblib"
VALID_SYMPTOMS_PATH = ARTIFACTS_DIR / "valid_symptoms.json"
DATASETS_DIR = ML_DIR / "datasets"


def _load_dataset(csv_path: Path) -> Tuple[List[str], List[str], List[str]]:
    """
    Load the CSV dataset and return (texts, labels, valid_symptoms_list).

    - symptom_* columns are combined into a single space-separated text field.
    - prognosis column is used as the label.
    - valid_symptoms_list is the unique set of non-empty symptom values
      (lower-cased) from all symptom_* columns.
    """
    df = pd.read_csv(csv_path)

    # Infer symptom columns by prefix
    symptom_cols = [c for c in df.columns if c.lower().startswith("symptom_")]
    if not symptom_cols:
        raise ValueError("No symptom_* columns found in dataset.")

    if "prognosis" not in df.columns:
        raise ValueError("Dataset must contain a 'prognosis' column.")

    texts: List[str] = []
    labels: List[str] = []
    all_symptoms_set = set()

    for _, row in df.iterrows():
        row_symptoms: List[str] = []
        for col in symptom_cols:
            val = row.get(col)
            if pd.isna(val):
                continue
            s = str(val).strip()
            if not s:
                continue
            s_lower = s.lower()
            row_symptoms.append(s_lower)
            all_symptoms_set.add(s_lower)

        if not row_symptoms:
            # Skip rows that have no symptoms at all
            continue

        text = " ".join(row_symptoms)
        label = str(row["prognosis"]).strip()
        if not label:
            continue

        texts.append(text)
        labels.append(label)

    if not texts:
        raise ValueError("No training examples could be constructed from the dataset.")

    valid_symptoms_list = sorted(all_symptoms_set)
    return texts, labels, valid_symptoms_list


def _build_pipeline() -> Pipeline:
    """Create the TF-IDF + MultinomialNB pipeline."""
    return Pipeline(
        [
            ("vec", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ("clf", MultinomialNB()),
        ]
    )


def train_from_csv(csv_filename: str) -> None:
    """
    Train the model from a CSV file located in `datasets/`.

    Example:
        python -m backend.app.ml.train_model my_dataset.csv
    """
    csv_path = DATASETS_DIR / csv_filename
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset CSV not found at {csv_path}")

    print(f"Loading dataset from: {csv_path}")
    texts, labels, valid_symptoms = _load_dataset(csv_path)
    print(f"Loaded {len(texts)} examples with {len(valid_symptoms)} unique symptoms.")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = _build_pipeline()
    print("Training TF-IDF + MultinomialNB pipeline...")
    pipeline.fit(X_train, y_train)

    print("Evaluating on held-out test set...")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {acc:.4f}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Saving trained model to: {MODEL_PATH}")
    joblib.dump(pipeline, MODEL_PATH)

    print(f"Saving valid symptoms list to: {VALID_SYMPTOMS_PATH}")
    with open(VALID_SYMPTOMS_PATH, "w", encoding="utf-8") as f:
        json.dump(valid_symptoms, f, ensure_ascii=False, indent=2)

    print("Training complete.")


def main() -> None:
    """
    CLI entrypoint.

    Usage examples (from project root):
        python -m backend.app.ml.train_model my_dataset.csv
    """
    import argparse

    parser = argparse.ArgumentParser(description="Train the MediAssist AI symptom model from a CSV dataset.")
    parser.add_argument(
        "csv_filename",
        help="CSV filename located in backend/app/ml/datasets/",
    )
    args = parser.parse_args()

    train_from_csv(args.csv_filename)


if __name__ == "__main__":
    # This script is run manually; it is **not** called automatically
    # from the Flask app. See the README or docstring for usage.
    main()

