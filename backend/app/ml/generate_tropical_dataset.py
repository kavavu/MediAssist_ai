"""
Generate synthetic training/testing datasets for the 15 tropical diseases
used by the Hybrid Clinical Prediction Engine.

This creates binary-encoded symptom datasets that match the clinical engine's
knowledge base, allowing the ML model to learn the same patterns.
"""
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Directory paths
ML_DIR = Path(__file__).resolve().parent
DATASETS_DIR = ML_DIR / "datasets"
DATASETS_DIR.mkdir(exist_ok=True)

# ============================================================
# DISEASE DEFINITIONS WITH CORE/SUPPORTING SYMPTOMS
# ============================================================

# Core symptoms = weight >= 4 (must-have for realistic cases)
# Supporting symptoms = weight >= 2 (common accompaniments)
# Rare symptoms = weight 1 (occasional)

DISEASE_PROFILES: Dict[str, Dict] = {
    "Malaria": {
        "core": ["fever", "high_fever", "chills", "shivering"],
        "supporting": ["headache", "vomiting", "nausea", "sweating", "fatigue", "weakness", "muscle_pain", "body_ache", "loss_of_appetite", "malaise"],
        "rare": ["abdominal_pain", "diarrhea"],
        "severity": "HIGH",
    },
    "Typhoid": {
        "core": ["fever", "high_fever", "abdominal_pain", "headache"],
        "supporting": ["loss_of_appetite", "weakness", "fatigue", "constipation", "diarrhea", "rose_spots", "nausea", "vomiting", "malaise"],
        "rare": [],
        "severity": "HIGH",
    },
    "Dengue": {
        "core": ["fever", "high_fever", "severe_headache", "pain_behind_eyes"],
        "supporting": ["muscle_pain", "joint_pain", "rash", "red_spots", "nausea", "vomiting", "fatigue", "weakness", "abdominal_pain"],
        "rare": ["blood_in_urine"],
        "severity": "HIGH",
    },
    "Pneumonia": {
        "core": ["cough", "persistent_cough", "fever", "high_fever", "shortness_of_breath", "difficulty_breathing"],
        "supporting": ["chest_pain", "chest_tightness", "fatigue", "weakness", "phlegm", "chills", "sweating", "loss_of_appetite"],
        "rare": ["confusion"],
        "severity": "HIGH",
    },
    "Flu": {
        "core": ["fever", "high_fever", "cough", "sore_throat", "body_ache", "muscle_pain"],
        "supporting": ["fatigue", "weakness", "headache", "chills", "runny_nose", "congestion", "sneezing", "nausea", "vomiting"],
        "rare": [],
        "severity": "MEDIUM",
    },
    "COVID-19": {
        "core": ["fever", "cough", "loss_of_smell", "loss_of_taste"],
        "supporting": ["fatigue", "shortness_of_breath", "difficulty_breathing", "sore_throat", "headache", "muscle_pain", "body_ache"],
        "rare": ["runny_nose", "congestion", "nausea", "vomiting", "diarrhea"],
        "severity": "MEDIUM",
    },
    "Gastroenteritis": {
        "core": ["diarrhea", "vomiting", "abdominal_pain"],
        "supporting": ["nausea", "fever", "high_fever", "dehydration", "weakness", "fatigue", "loss_of_appetite", "headache", "muscle_pain"],
        "rare": [],
        "severity": "MEDIUM",
    },
    "Food_Poisoning": {
        "core": ["nausea", "vomiting", "diarrhea", "abdominal_cramps", "abdominal_pain"],
        "supporting": ["fever", "weakness", "fatigue", "dehydration", "loss_of_appetite", "headache"],
        "rare": [],
        "severity": "MEDIUM",
    },
    "Tuberculosis": {
        "core": ["persistent_cough", "cough", "weight_loss", "night_sweats", "bloody_phlegm"],
        "supporting": ["fever", "high_fever", "fatigue", "weakness", "chest_pain", "loss_of_appetite", "shortness_of_breath", "difficulty_breathing"],
        "rare": [],
        "severity": "HIGH",
    },
    "Asthma": {
        "core": ["wheezing", "shortness_of_breath", "difficulty_breathing", "cough"],
        "supporting": ["chest_tightness", "chest_pain", "fatigue", "weakness", "phlegm"],
        "rare": [],
        "severity": "MEDIUM",
    },
    "UTI": {
        "core": ["burning_urination", "frequent_urination", "blood_in_urine"],
        "supporting": ["pelvic_pain", "foul_urine", "abdominal_pain", "fever", "nausea", "vomiting", "back_pain"],
        "rare": [],
        "severity": "MEDIUM",
    },
    "Chickenpox": {
        "core": ["itchy_rash", "rash", "red_spots", "fever"],
        "supporting": ["fatigue", "loss_of_appetite", "headache", "muscle_pain", "nausea", "abdominal_pain"],
        "rare": [],
        "severity": "LOW",
    },
    "Common_Cold": {
        "core": ["runny_nose", "sneezing", "sore_throat", "cough"],
        "supporting": ["congestion", "headache", "fatigue", "mild_fever", "fever", "watering_from_eyes"],
        "rare": [],
        "severity": "LOW",
    },
    "Meningitis": {
        "core": ["fever", "high_fever", "stiff_neck", "severe_headache", "confusion", "altered_consciousness"],
        "supporting": ["vomiting", "sensitivity_to_light", "fatigue", "weakness", "rash", "seizure"],
        "rare": [],
        "severity": "HIGH",
    },
    "Diabetes_Warning": {
        "core": ["excessive_thirst", "polydipsia", "frequent_urination", "polyuria"],
        "supporting": ["fatigue", "weight_loss", "blurred_vision", "slow_healing", "frequent_infections", "excessive_hunger"],
        "rare": ["numbness", "tingling"],
        "severity": "MEDIUM",
    },
}

# All possible symptoms (union of all symptoms across diseases)
ALL_SYMPTOMS = sorted({
    s for profile in DISEASE_PROFILES.values()
    for group in ["core", "supporting", "rare"]
    for s in profile[group]
})

print(f"Total unique symptoms: {len(ALL_SYMPTOMS)}")
print(f"Total diseases: {len(DISEASE_PROFILES)}")


def generate_case(disease: str, noise_prob: float = 0.05) -> Dict[str, int]:
    """
    Generate a single synthetic case for a disease.

    Rules:
    - 100% of core symptoms present
    - 70-90% of supporting symptoms present
    - 0-30% of rare symptoms present
    - Small noise: random unrelated symptoms may appear
    """
    profile = DISEASE_PROFILES[disease]
    symptoms = {s: 0 for s in ALL_SYMPTOMS}

    # Core symptoms: always present
    for s in profile["core"]:
        symptoms[s] = 1

    # Supporting symptoms: 70-90% present
    for s in profile["supporting"]:
        if random.random() < random.uniform(0.7, 0.9):
            symptoms[s] = 1

    # Rare symptoms: 0-30% present
    for s in profile["rare"]:
        if random.random() < random.uniform(0.0, 0.3):
            symptoms[s] = 1

    # Noise: occasional unrelated symptom
    unrelated = [s for s in ALL_SYMPTOMS if symptoms[s] == 0]
    if unrelated and random.random() < noise_prob:
        noise_symptom = random.choice(unrelated)
        symptoms[noise_symptom] = 1

    return symptoms


def generate_dataset(n_per_disease: int = 150, test_split: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate training and testing datasets."""
    random.seed(42)

    train_rows = []
    test_rows = []

    for disease in DISEASE_PROFILES:
        for i in range(n_per_disease):
            case = generate_case(disease, noise_prob=0.08)
            case["prognosis"] = disease

            if i < int(n_per_disease * (1 - test_split)):
                train_rows.append(case)
            else:
                test_rows.append(case)

    train_df = pd.DataFrame(train_rows)
    test_df = pd.DataFrame(test_rows)

    # Shuffle
    train_df = train_df.sample(frac=1, random_state=42).reset_index(drop=True)
    test_df = test_df.sample(frac=1, random_state=42).reset_index(drop=True)

    return train_df, test_df


def save_datasets(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Save datasets to CSV files."""
    train_path = DATASETS_DIR / "Training_Tropical.csv"
    test_path = DATASETS_DIR / "Testing_Tropical.csv"

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"Training set: {len(train_df)} rows -> {train_path}")
    print(f"Testing set:  {len(test_df)} rows -> {test_path}")

    # Print class distribution
    print("\nClass distribution (training):")
    for disease, count in train_df["prognosis"].value_counts().sort_index().items():
        print(f"  {disease}: {count}")


def save_symptom_list() -> None:
    """Save the list of valid symptoms for reference."""
    symptoms_path = ML_DIR / "artifacts" / "valid_symptoms_tropical.json"
    symptoms_path.parent.mkdir(exist_ok=True)

    with open(symptoms_path, "w", encoding="utf-8") as f:
        json.dump(ALL_SYMPTOMS, f, indent=2)

    print(f"Symptom list saved: {symptoms_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Generating Tropical Disease Dataset")
    print("=" * 60)

    train_df, test_df = generate_dataset(n_per_disease=150, test_split=0.2)
    save_datasets(train_df, test_df)
    save_symptom_list()

    print("\n" + "=" * 60)
    print("Dataset generation complete!")
    print("=" * 60)
