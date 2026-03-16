"""
Symptom classification model using scikit-learn.

Current behaviour:
------------------
- On first use, loads a persisted model from artifacts/symptom_model.joblib.
- If no persisted model exists yet, trains a simple placeholder model on a
  small hard-coded dataset and saves it.

Extensions for safer, more academic usage:
------------------------------------------
- Support for training on a real dataset via backend/app/ml/train_model.py
- Optional loading of a valid_symptoms.json list for spell correction and
  symptom validation.
- Utility to return the top-k predictions with confidence scores.

The existing `predict(text)` function is kept for backwards compatibility and
still returns a single (condition, confidence) tuple. Higher-level services
use `predict_topk(...)` for richer behaviour.
"""

from __future__ import annotations

import json
import os
from difflib import get_close_matches
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Directory for persisted model (next to this module)
_ML_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_ML_DIR, "artifacts", "symptom_model.joblib")
_VALID_SYMPTOMS_PATH = os.path.join(_ML_DIR, "artifacts", "valid_symptoms.json")

# Placeholder dataset: (symptoms text, condition) for initial training
_PLACEHOLDER_DATA = [
    ("headache fever body ache tired", "flu"),
    ("headache fever chills cough", "flu"),
    ("runny nose sneezing sore throat", "common_cold"),
    ("cough congestion runny nose", "common_cold"),
    ("stomach pain nausea vomiting", "gastric"),
    ("abdominal pain bloating indigestion", "gastric"),
    ("chest pain shortness of breath", "cardiac_concern"),
    ("dizziness fatigue weakness", "fatigue"),
    ("sore throat fever swollen glands", "strep_throat"),
    ("rash itching skin redness", "skin_allergy"),
    ("joint pain swelling stiffness", "arthritis"),
    ("back pain muscle ache", "musculoskeletal"),
    ("headache only mild", "tension_headache"),
    ("fever only high temperature", "fever"),
    ("cough only dry cough", "cough"),
]

# Cached state; set once by loaders on first use
_pipeline: Optional[Pipeline] = None
_valid_symptoms: Optional[List[str]] = None


def _train_and_save(path: str) -> Pipeline:
    """Train TfidfVectorizer + MultinomialNB on _PLACEHOLDER_DATA, save as joblib file."""
    texts = [t for t, _ in _PLACEHOLDER_DATA]
    labels = [c for _, c in _PLACEHOLDER_DATA]
    pipeline = Pipeline(
        [
            ("vec", TfidfVectorizer(max_features=500, ngram_range=(1, 2))),
            ("clf", MultinomialNB()),
        ]
    )
    pipeline.fit(texts, labels)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(pipeline, path)
    return pipeline


def load_model() -> Pipeline:
    """
    Load the symptom classification model from disk.
    If the file does not exist, train with placeholder data and save.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if os.path.isfile(_MODEL_PATH):
        _pipeline = joblib.load(_MODEL_PATH)
    else:
        _pipeline = _train_and_save(_MODEL_PATH)
    return _pipeline


def _infer_valid_symptoms_from_placeholder() -> List[str]:
    """Derive a basic valid-symptom vocabulary from the placeholder dataset."""
    vocab = set()
    for text, _ in _PLACEHOLDER_DATA:
        for token in text.lower().split():
            token = token.strip()
            if token:
                vocab.add(token)
    return sorted(vocab)


def load_valid_symptoms() -> List[str]:
    """
    Load the valid symptoms list from artifacts/valid_symptoms.json.

    If the file does not exist yet (e.g. real dataset not trained), fall back
    to a vocabulary derived from the placeholder dataset. This keeps the system
    working today while allowing a richer list once a real dataset is used.
    """
    global _valid_symptoms
    if _valid_symptoms is not None:
        return _valid_symptoms

    if os.path.isfile(_VALID_SYMPTOMS_PATH):
        try:
            with open(_VALID_SYMPTOMS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                _valid_symptoms = sorted({str(s).strip().lower() for s in data if str(s).strip()})
            else:
                _valid_symptoms = _infer_valid_symptoms_from_placeholder()
        except (OSError, json.JSONDecodeError):
            _valid_symptoms = _infer_valid_symptoms_from_placeholder()
    else:
        _valid_symptoms = _infer_valid_symptoms_from_placeholder()

    return _valid_symptoms


def _tokenize(symptoms_text: str) -> List[str]:
    """
    Basic tokenizer: split on whitespace and commas, lower-case, drop empties.
    """
    if not symptoms_text:
        return []
    raw = symptoms_text.replace(",", " ")
    tokens = [t.strip().lower() for t in raw.split()]
    return [t for t in tokens if t]


def _correct_tokens(tokens: Sequence[str], valid_symptoms: Sequence[str], cutoff: float = 0.8) -> List[str]:
    """
    Apply simple spell correction using difflib.get_close_matches.

    For each token, if a close match exists in valid_symptoms above the cutoff,
    use the closest match; otherwise keep the original token.
    """
    corrected: List[str] = []
    vocab = list(valid_symptoms)
    for tok in tokens:
        matches = get_close_matches(tok, vocab, n=1, cutoff=cutoff)
        if matches:
            corrected.append(matches[0])
        else:
            corrected.append(tok)
    return corrected


def _validate_tokens(tokens: Sequence[str], valid_symptoms: Sequence[str]) -> bool:
    """
    Check that at least one token matches the known symptoms list.
    """
    valid_set = set(valid_symptoms)
    return any(t in valid_set for t in tokens)


def predict(symptoms_text: str) -> tuple:
    """
    Backwards-compatible prediction helper.

    Given symptoms text, return (predicted_condition, confidence_score).
    Confidence is 0.0 to 1.0.

    This does **not** expose validation information or multiple predictions.
    Newer code should use `predict_topk` instead.
    """
    pipe = load_model()
    if not (symptoms_text or "").strip():
        return None, 0.0
    text = (symptoms_text or "").strip()
    pred = pipe.predict([text])
    proba = pipe.predict_proba([text])
    condition = pred[0]
    confidence = float(proba.max())
    return condition, confidence


def predict_topk(
    symptoms_text: str,
    k: int = 3,
    confidence_threshold: float = 0.40,
) -> Dict[str, object]:
    """
    Rich prediction helper used by the service layer.

    Returns a dict with keys:
      - "cleaned_text": the normalized, spell-corrected symptom string
      - "predictions": list of { "condition": str, "confidence": float }
      - "low_confidence": bool (True if top prediction < threshold)

    In case of unrecognized symptoms, returns:
      - {"error": "Symptoms not recognized. Please enter valid medical symptoms."}
    """
    text = (symptoms_text or "").strip()
    if not text:
        return {
            "cleaned_text": "",
            "predictions": [],
            "low_confidence": True,
        }

    valid_symptoms = load_valid_symptoms()
    raw_tokens = _tokenize(text)
    corrected_tokens = _correct_tokens(raw_tokens, valid_symptoms)

    # Validate against known symptom vocabulary
    if not _validate_tokens(corrected_tokens, valid_symptoms):
        return {
            "error": "Symptoms not recognized. Please enter valid medical symptoms."
        }

    cleaned_text = " ".join(corrected_tokens)

    pipe = load_model()
    proba = pipe.predict_proba([cleaned_text])[0]
    classes = list(pipe.classes_)

    # Pair up conditions with probabilities and sort descending
    scored = sorted(
        [{"condition": cls, "confidence": float(p)} for cls, p in zip(classes, proba)],
        key=lambda x: x["confidence"],
        reverse=True,
    )

    top = scored[: max(1, k)]
    top_conf = top[0]["confidence"] if top else 0.0
    low_confidence = top_conf < confidence_threshold

    return {
        "cleaned_text": cleaned_text,
        "predictions": top,
        "low_confidence": low_confidence,
    }
