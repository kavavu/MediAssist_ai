"""
Hybrid Clinical Prediction Engine for MediAssist AI.

This module provides the PRIMARY prediction logic for the symptom checker.
It replaces the ML-first approach with a rule-based weighted symptom scoring
system focused on tropical diseases relevant to Kenya and East Africa.

Architecture:
    User Input → Advanced Normalization → Symptom Extraction →
        → Rule-Based Weighted Scoring (PRIMARY) →
        → ML Fallback (supporting) →
        → Confidence Calibration →
        → Red Flag Detection →
        → Top-3 Ranking + Clinical Insights → API Response

Diseases covered (15):
    Malaria, Typhoid, Dengue, Pneumonia, Flu, COVID-19,
    Gastroenteritis, Food Poisoning, Tuberculosis, Asthma,
    UTI, Chickenpox, Common Cold, Meningitis, Diabetes Warning
"""

from __future__ import annotations

import json
import logging
import os
import re
from difflib import get_close_matches
from typing import Dict, List, Optional, Tuple, Set

logger = logging.getLogger(__name__)

# ============================================================
# SECTION 1 — TROPICAL DISEASE KNOWLEDGE BASE
# ============================================================

# Canonical symptom names used across the engine
_CANONICAL_SYMPTOMS: Set[str] = {
    "fever", "high fever", "chills", "shivering", "sweating", "night sweats",
    "headache", "severe headache", "pain behind eyes",
    "vomiting", "nausea", "diarrhea", "constipation", "abdominal pain", "abdominal cramps",
    "loss of appetite", "weight loss", "fatigue", "weakness", "dehydration",
    "muscle pain", "joint pain", "body ache", "back pain",
    "cough", "persistent cough", "phlegm", "bloody phlegm", "wheezing",
    "shortness of breath", "difficulty breathing", "chest pain", "chest tightness",
    "sore throat", "runny nose", "sneezing", "congestion", "loss of smell", "loss of taste",
    "rash", "itchy rash", "red spots", "rose spots",
    "burning urination", "frequent urination", "blood in urine", "foul urine", "pelvic pain",
    "stiff neck", "confusion", "sensitivity to light", "seizure", "altered consciousness",
    "blurred vision", "slow healing", "excessive thirst", "polydipsia",
    "dizziness", "palpitations", "fast heart rate",
    "yellowish skin", "jaundice", "dark urine",
    "cold hands and feet", "malaise", "excessive hunger", "polyphagia",
    "frequent infections", "numbness", "tingling",
}

# Disease definitions with weighted symptoms
# Weights: 5=critical/pathognomonic, 4=core, 3=common, 2=supporting, 1=rare
_DISEASE_KB: Dict[str, Dict] = {
    "Malaria": {
        "symptom_weights": {
            "fever": 5, "high fever": 5, "chills": 4, "shivering": 4,
            "headache": 3, "vomiting": 3, "nausea": 2,
            "sweating": 2, "fatigue": 2, "weakness": 2,
            "muscle pain": 2, "body ache": 2, "loss of appetite": 2,
            "malaise": 2, "abdominal pain": 1, "diarrhea": 1,
        },
        "severity": "HIGH",
        "emergency_indicators": {"confusion", "altered consciousness", "severe weakness", "high fever", "seizure"},
        "recommended_tests": [
            "Thick and thin blood smear",
            "Rapid diagnostic test (RDT) for malaria",
            "Complete Blood Count (CBC)",
        ],
        "clinical_insight": (
            "Malaria is a mosquito-borne disease caused by Plasmodium parasites. "
            "It is endemic in Kenya and presents with cyclical fever, chills, and sweating. "
            "Prompt diagnosis and treatment are essential to prevent complications."
        ),
        "category": "infectious",
    },
    "Typhoid": {
        "symptom_weights": {
            "fever": 5, "high fever": 5, "abdominal pain": 4, "headache": 3,
            "loss of appetite": 3, "weakness": 2, "fatigue": 2,
            "constipation": 2, "diarrhea": 2, "rose spots": 3,
            "nausea": 2, "vomiting": 2, "malaise": 2,
        },
        "severity": "HIGH",
        "emergency_indicators": {"severe abdominal pain", "bleeding", "altered consciousness", "high fever"},
        "recommended_tests": [
            "Blood culture",
            "Widal serology",
            "CBC with differential",
            "Stool culture (if indicated)",
        ],
        "clinical_insight": (
            "Typhoid fever is a bacterial infection caused by Salmonella typhi, often transmitted "
            "through contaminated food or water. It presents with sustained fever, abdominal discomfort, "
            "and systemic symptoms. Early antibiotic therapy reduces complications."
        ),
        "category": "infectious",
    },
    "Dengue": {
        "symptom_weights": {
            "fever": 5, "high fever": 5, "severe headache": 4, "pain behind eyes": 4,
            "muscle pain": 3, "joint pain": 3, "rash": 3, "red spots": 3,
            "nausea": 2, "vomiting": 2, "fatigue": 2, "weakness": 2,
            "bleeding": 3, "blood in urine": 2, "abdominal pain": 2,
        },
        "severity": "HIGH",
        "emergency_indicators": {"severe bleeding", "persistent vomiting", "altered consciousness", "difficulty breathing"},
        "recommended_tests": [
            "Dengue NS1 antigen test",
            "Dengue IgM/IgG serology",
            "CBC (platelet count critical)",
            "Hematocrit monitoring",
        ],
        "clinical_insight": (
            "Dengue is a viral infection transmitted by Aedes mosquitoes. Watch for warning signs "
            "of plasma leakage and bleeding (dengue hemorrhagic fever). Platelet monitoring is critical."
        ),
        "category": "infectious",
    },
    "Pneumonia": {
        "symptom_weights": {
            "cough": 4, "persistent cough": 4, "fever": 4, "high fever": 4,
            "shortness of breath": 4, "difficulty breathing": 4,
            "chest pain": 3, "chest tightness": 3,
            "fatigue": 2, "weakness": 2, "phlegm": 2, "bloody phlegm": 3,
            "chills": 2, "sweating": 2, "loss of appetite": 1, "confusion": 2,
        },
        "severity": "HIGH",
        "emergency_indicators": {"severe shortness of breath", "cyanosis", "altered consciousness", "chest pain"},
        "recommended_tests": [
            "Chest X-ray",
            "CBC",
            "Sputum culture",
            "Blood culture",
            "Pulse oximetry",
        ],
        "clinical_insight": (
            "Pneumonia is an infection that inflames the air sacs in one or both lungs. "
            "It can range from mild to life-threatening, especially in children, elderly, and immunocompromised patients."
        ),
        "category": "respiratory",
    },
    "Flu": {
        "symptom_weights": {
            "fever": 4, "high fever": 4, "cough": 3, "sore throat": 3,
            "body ache": 3, "muscle pain": 3, "fatigue": 2, "weakness": 2,
            "headache": 2, "chills": 2, "runny nose": 2, "congestion": 2,
            "sneezing": 1, "nausea": 1, "vomiting": 1,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"difficulty breathing", "chest pain", "altered consciousness", "severe weakness"},
        "recommended_tests": [
            "Rapid influenza test (if within 48 hours)",
            "CBC",
            "Chest X-ray (if pneumonia suspected)",
        ],
        "clinical_insight": (
            "Influenza is a viral respiratory infection that can cause severe complications in high-risk groups. "
            "It spreads rapidly and is common during rainy seasons in Kenya."
        ),
        "category": "respiratory",
    },
    "COVID-19": {
        "symptom_weights": {
            "fever": 4, "cough": 4, "loss of smell": 4, "loss of taste": 4,
            "fatigue": 3, "shortness of breath": 3, "difficulty breathing": 3,
            "sore throat": 2, "headache": 2, "muscle pain": 2, "body ache": 2,
            "runny nose": 1, "congestion": 1, "nausea": 1, "vomiting": 1, "diarrhea": 1,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"severe shortness of breath", "chest pain", "altered consciousness", "cyanosis"},
        "recommended_tests": [
            "RT-PCR or rapid antigen test",
            "CBC",
            "CRP",
            "Chest X-ray (if respiratory distress)",
        ],
        "clinical_insight": (
            "COVID-19 is caused by SARS-CoV-2. Severity ranges from asymptomatic to severe pneumonia. "
            "Monitor oxygen saturation and seek care for respiratory distress."
        ),
        "category": "respiratory",
    },
    "Gastroenteritis": {
        "symptom_weights": {
            "diarrhea": 4, "vomiting": 4, "abdominal pain": 3, "nausea": 2,
            "fever": 2, "high fever": 2, "dehydration": 2, "weakness": 2,
            "fatigue": 1, "loss of appetite": 1, "headache": 1, "muscle pain": 1,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"bloody stool", "severe dehydration", "altered consciousness", "persistent vomiting"},
        "recommended_tests": [
            "Stool culture (if severe or bloody)",
            "CBC",
            "Electrolyte panel",
            "Oral rehydration assessment",
        ],
        "clinical_insight": (
            "Gastroenteritis is inflammation of the stomach and intestines, usually infectious in origin. "
            "Dehydration is the main risk—oral rehydration therapy is first-line treatment."
        ),
        "category": "gastrointestinal",
    },
    "Food Poisoning": {
        "symptom_weights": {
            "nausea": 4, "vomiting": 4, "diarrhea": 4, "abdominal cramps": 3,
            "abdominal pain": 3, "fever": 2, "weakness": 2, "fatigue": 1,
            "headache": 1, "dehydration": 2, "loss of appetite": 1,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"bloody vomit", "bloody stool", "severe dehydration", "altered consciousness"},
        "recommended_tests": [
            "Stool culture",
            "Blood culture (if high fever)",
            "CBC and electrolytes",
        ],
        "clinical_insight": (
            "Food poisoning results from consuming contaminated food or water. Symptoms typically appear "
            "within hours and include nausea, vomiting, and diarrhea. Hydration is critical."
        ),
        "category": "gastrointestinal",
    },
    "Tuberculosis": {
        "symptom_weights": {
            "persistent cough": 5, "cough": 4, "weight loss": 4, "night sweats": 4,
            "fever": 3, "high fever": 3, "fatigue": 3, "weakness": 2,
            "bloody phlegm": 4, "blood in sputum": 4, "chest pain": 2,
            "loss of appetite": 2, "shortness of breath": 2, "difficulty breathing": 2,
        },
        "severity": "HIGH",
        "emergency_indicators": {"severe bleeding", "severe shortness of breath", "altered consciousness"},
        "recommended_tests": [
            "Sputum AFB smear and culture",
            "Chest X-ray",
            "GeneXpert MTB/RIF (if available)",
            "CBC and ESR",
        ],
        "clinical_insight": (
            "Tuberculosis is a bacterial infection primarily affecting the lungs. Chronic cough (>2 weeks), "
            "weight loss, and night sweats are classic. It is a major public health concern in Kenya."
        ),
        "category": "infectious",
    },
    "Asthma": {
        "symptom_weights": {
            "wheezing": 5, "shortness of breath": 4, "difficulty breathing": 4,
            "cough": 3, "chest tightness": 3, "chest pain": 2,
            "fatigue": 1, "weakness": 1, "phlegm": 1,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"severe shortness of breath", "cyanosis", "altered consciousness", "inability to speak"},
        "recommended_tests": [
            "Peak expiratory flow measurement",
            "Spirometry",
            "Chest X-ray (if first episode)",
        ],
        "clinical_insight": (
            "Asthma is a chronic inflammatory disease of the airways characterized by reversible airflow obstruction. "
            "Trigger avoidance and proper inhaler use are essential for control."
        ),
        "category": "respiratory",
    },
    "UTI": {
        "symptom_weights": {
            "burning urination": 5, "frequent urination": 3, "blood in urine": 3,
            "pelvic pain": 2, "foul urine": 2, "abdominal pain": 2,
            "fever": 2, "nausea": 1, "vomiting": 1, "back pain": 2,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"fever", "back pain", "altered consciousness", "severe weakness"},
        "recommended_tests": [
            "Urinalysis and urine culture",
            "CBC",
            "Renal function tests (if complicated)",
        ],
        "clinical_insight": (
            "A urinary tract infection (UTI) can affect the bladder (cystitis) or kidneys (pyelonephritis). "
            "Fever with back pain suggests kidney involvement and needs urgent evaluation."
        ),
        "category": "urinary",
    },
    "Chickenpox": {
        "symptom_weights": {
            "itchy rash": 5, "rash": 4, "red spots": 3, "fever": 3,
            "fatigue": 2, "loss of appetite": 2, "headache": 2,
            "muscle pain": 1, "nausea": 1, "abdominal pain": 1,
        },
        "severity": "LOW",
        "emergency_indicators": {"severe rash", "difficulty breathing", "altered consciousness", "high fever"},
        "recommended_tests": [
            "Clinical diagnosis (typical presentation)",
            "Viral PCR or culture (if atypical)",
        ],
        "clinical_insight": (
            "Chickenpox is a highly contagious viral infection causing an itchy, blister-like rash. "
            "It is usually self-limiting but can be severe in adults and immunocompromised individuals."
        ),
        "category": "infectious",
    },
    "Common Cold": {
        "symptom_weights": {
            "runny nose": 4, "sneezing": 4, "sore throat": 3, "cough": 2,
            "congestion": 2, "mild headache": 2, "headache": 1,
            "fatigue": 1, "mild fever": 1, "fever": 1, "watering from eyes": 1,
        },
        "severity": "LOW",
        "emergency_indicators": set(),
        "recommended_tests": [
            "Clinical diagnosis",
            "Rapid strep test (if sore throat prominent)",
        ],
        "clinical_insight": (
            "The common cold is a viral infection of the upper respiratory tract, usually self-limiting. "
            "Rest, hydration, and symptomatic relief are usually sufficient."
        ),
        "category": "respiratory",
    },
    "Meningitis": {
        "symptom_weights": {
            "fever": 5, "high fever": 5, "stiff neck": 5, "severe headache": 4,
            "confusion": 4, "altered consciousness": 4, "vomiting": 3,
            "sensitivity to light": 3, "fatigue": 2, "weakness": 2,
            "rash": 2, "seizure": 4,
        },
        "severity": "HIGH",
        "emergency_indicators": {"seizure", "altered consciousness", "severe confusion", "high fever"},
        "recommended_tests": [
            "Lumbar puncture (CSF analysis)",
            "Blood culture",
            "CBC and CRP",
            "CT brain (before LP if indicated)",
        ],
        "clinical_insight": (
            "Meningitis is inflammation of the membranes surrounding the brain and spinal cord. "
            "It is a medical emergency requiring rapid diagnosis and treatment to prevent brain damage or death."
        ),
        "category": "neurological",
    },
    "Diabetes Warning": {
        "symptom_weights": {
            "excessive thirst": 4, "polydipsia": 4, "frequent urination": 4, "polyuria": 4,
            "fatigue": 3, "weight loss": 3, "blurred vision": 2,
            "slow healing": 2, "frequent infections": 2, "numbness": 1,
            "tingling": 1, "excessive hunger": 2,
        },
        "severity": "MEDIUM",
        "emergency_indicators": {"severe dehydration", "altered consciousness", "confusion", "vomiting"},
        "recommended_tests": [
            "Fasting blood glucose",
            "HbA1c",
            "Urine ketones",
            "Renal function tests",
        ],
        "clinical_insight": (
            "These symptoms may indicate diabetes mellitus, a chronic metabolic disorder with elevated blood sugar. "
            "Early detection and glycemic control prevent complications affecting the eyes, kidneys, nerves, and heart."
        ),
        "category": "endocrine",
    },
}

# Pre-compute max possible scores for each disease
_DISEASE_MAX_SCORES: Dict[str, float] = {}
for _dname, _dinfo in _DISEASE_KB.items():
    _DISEASE_MAX_SCORES[_dname] = sum(_dinfo["symptom_weights"].values())


# ============================================================
# SECTION 2 — ADVANCED INPUT NORMALIZATION
# ============================================================

# Expanded aliases including Kenyan/local phrasing, slang, and common misspellings
_SYMPTOM_ALIASES: Dict[str, str] = {
    # === Misspellings ===
    "vomitting": "vomiting",
    "vomitted": "vomiting",
    "diarrhoea": "diarrhea",
    "diarhea": "diarrhea",
    "diarhoea": "diarrhea",
    "feverish": "fever",
    "febrile": "fever",
    "cought": "cough",
    "coughing": "cough",
    "coughin": "cough",
    "headach": "headache",
    "headace": "headache",
    "headche": "headache",
    "stomachache": "abdominal pain",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "tummy pain": "abdominal pain",
    "belly pain": "abdominal pain",
    "tumbo kuumwa": "abdominal pain",
    "pain in stomach": "abdominal pain",
    "pain in abdomen": "abdominal pain",
    "abdominal cramps": "abdominal cramps",
    "stomach cramps": "abdominal cramps",
    "tummy cramps": "abdominal cramps",
    "backpain": "back pain",
    "back ache": "back pain",
    "back hurting": "back pain",
    "my back hurts": "back pain",
    "pain in back": "back pain",
    "chestpain": "chest pain",
    "chest pain": "chest pain",
    "chest tightness": "chest tightness",
    "my chest feels tight": "chest tightness",
    "tight chest": "chest tightness",
    "chest discomfort": "chest pain",
    "pain in chest": "chest pain",
    "musclepain": "muscle pain",
    "muscle ache": "muscle pain",
    "muscles hurt": "muscle pain",
    "body pain": "muscle pain",
    "body ache": "muscle pain",
    "body aches": "muscle pain",
    "pain all over": "muscle pain",
    "aching all over": "muscle pain",
    "aching body": "muscle pain",
    "sorethroat": "sore throat",
    "sore throat": "sore throat",
    "throat pain": "sore throat",
    "painful throat": "sore throat",
    "scratchy throat": "sore throat",
    "throat hurts": "sore throat",
    "hurting throat": "sore throat",
    # === Fever / temperature ===
    "high temp": "fever",
    "temperature": "fever",
    "very hot body": "high fever",
    "hot body": "fever",
    "running temperature": "fever",
    "feeling hot": "fever",
    "burning up": "fever",
    "homakali": "high fever",
    "homa kali": "high fever",
    "joto kali": "high fever",
    "mild fever": "fever",
    "very high fever": "high fever",
    # === Respiratory ===
    "persistent cough": "persistent cough",
    "dry cough": "cough",
    "wet cough": "cough",
    "hacking cough": "cough",
    "phlegm": "phlegm",
    "mucus": "phlegm",
    "mucus in throat": "phlegm",
    "bloody phlegm": "bloody phlegm",
    "blood in sputum": "bloody phlegm",
    "rusty sputum": "bloody phlegm",
    # === Breathing ===
    "shortnessofbreath": "shortness of breath",
    "short of breath": "shortness of breath",
    "cant breathe": "difficulty breathing",
    "can't breathe": "difficulty breathing",
    "cannot breathe": "difficulty breathing",
    "hard to breathe": "difficulty breathing",
    "breathlessness": "shortness of breath",
    "labored breathing": "difficulty breathing",
    "gasping": "difficulty breathing",
    "trouble breathing": "difficulty breathing",
    "difficulty in breathing": "difficulty breathing",
    "severe shortness of breath": "difficulty breathing",
    # === GI ===
    "nauseous": "nausea",
    "feel sick": "nausea",
    "feeling sick": "nausea",
    "queasy": "nausea",
    "nauseated": "nausea",
    "throwing up": "vomiting",
    "puking": "vomiting",
    "throw up": "vomiting",
    "threw up": "vomiting",
    "loose stools": "diarrhea",
    "watery stool": "diarrhea",
    "loose motion": "diarrhea",
    "frequent stools": "diarrhea",
    "running stomach": "diarrhea",
    "tumbo inaenda": "diarrhea",
    "constipated": "constipation",
    "cant poop": "constipation",
    "can't poop": "constipation",
    # === ENT ===
    "runnynose": "runny nose",
    "runny nose": "runny nose",
    "dripping nose": "runny nose",
    "blockednose": "congestion",
    "stuffy nose": "congestion",
    "blocked nose": "congestion",
    "nasal blockage": "congestion",
    "congested nose": "congestion",
    "sneazing": "sneezing",
    "sneeze": "sneezing",
    # === Neuro / general ===
    "dizzy": "dizziness",
    "lightheaded": "dizziness",
    "spinning head": "dizziness",
    "feeling faint": "dizziness",
    "woozy": "dizziness",
    "tired": "fatigue",
    "tired all the time": "fatigue",
    "exhausted": "fatigue",
    "no energy": "fatigue",
    "feeling weak": "weakness",
    "weakness": "weakness",
    "lethargic": "fatigue",
    "low energy": "fatigue",
    "worn out": "fatigue",
    "drained": "fatigue",
    "kuchoka": "fatigue",
    "kuchoka sana": "fatigue",
    "uchovu": "fatigue",
    # === Chills / sweating ===
    "chills": "chills",
    "shivering": "chills",
    "shivering badly": "chills",
    "rigors": "chills",
    "sweating": "sweating",
    "sweats": "sweating",
    "excessive sweating": "sweating",
    "night sweats": "night sweats",
    "baridi kali": "chills",
    "kutetemeka": "chills",
    # === Skin ===
    "rash": "rash",
    "skin rash": "rash",
    "red spots": "red spots",
    "spots on skin": "red spots",
    "skin eruption": "rash",
    "itching": "itchy rash",
    "itchy": "itchy rash",
    "pruritus": "itchy rash",
    "itchy skin": "itchy rash",
    "skin itching": "itchy rash",
    "rose spots": "rose spots",
    # === Swelling / edema ===
    "swelling": "swelling",
    "swollen": "swelling",
    "puffy": "swelling",
    "edema": "swelling",
    "bloated": "swelling",
    # === Appetite / weight ===
    "loss of appetite": "loss of appetite",
    "not hungry": "loss of appetite",
    "no appetite": "loss of appetite",
    "appetite loss": "loss of appetite",
    "sikupendi kula": "loss of appetite",
    "weight loss": "weight loss",
    "losing weight": "weight loss",
    "unintended weight loss": "weight loss",
    "excessive hunger": "excessive hunger",
    "always hungry": "excessive hunger",
    "polyphagia": "excessive hunger",
    # === Bleeding / excretion ===
    "blood in stool": "bloody stool",
    "bloody stool": "bloody stool",
    "blood in urine": "blood in urine",
    "bloody urine": "blood in urine",
    "pain when peeing": "burning urination",
    "painful urination": "burning urination",
    "burning when peeing": "burning urination",
    "burning while urinating": "burning urination",
    "kukojoa uchungu": "burning urination",
    "kukojoa mara nyingi": "frequent urination",
    "foul smell of urine": "foul urine",
    "smelly urine": "foul urine",
    # === Vision / neuro ===
    "blurred vision": "blurred vision",
    "cant see clearly": "blurred vision",
    "can't see clearly": "blurred vision",
    "cloudy vision": "blurred vision",
    "fuzzy vision": "blurred vision",
    "confusion": "confusion",
    "disoriented": "confusion",
    "confused": "confusion",
    "cant think straight": "confusion",
    "can't think straight": "confusion",
    "mental fog": "confusion",
    "sensitivity to light": "sensitivity to light",
    "light hurts eyes": "sensitivity to light",
    # === Consciousness ===
    "seizure": "seizure",
    "convulsion": "seizure",
    "fit": "seizure",
    "kiharusi": "seizure",
    "fainting": "altered consciousness",
    "passed out": "altered consciousness",
    "passing out": "altered consciousness",
    "syncope": "altered consciousness",
    "unconscious": "altered consciousness",
    "knocked out": "altered consciousness",
    "loss of consciousness": "altered consciousness",
    "unresponsive": "altered consciousness",
    "altered sensorium": "altered consciousness",
    # === Cardiac ===
    "palpitations": "palpitations",
    "racing heart": "palpitations",
    "heart racing": "palpitations",
    "heart pounding": "palpitations",
    "skipped beats": "palpitations",
    "fluttering heart": "palpitations",
    "fast heart rate": "fast heart rate",
    "rapid heartbeat": "fast heart rate",
    "rapid heart rate": "fast heart rate",
    # === Dehydration ===
    "dehydration": "dehydration",
    "dry mouth": "dehydration",
    "very thirsty": "excessive thirst",
    "extreme thirst": "excessive thirst",
    "kunywa maji sana": "excessive thirst",
    # === Diabetes specific ===
    "polydipsia": "polydipsia",
    "drinking a lot": "polydipsia",
    "polyuria": "frequent urination",
    "peeing a lot": "frequent urination",
    "frequent urination": "frequent urination",
    "slow healing wounds": "slow healing",
    "wounds not healing": "slow healing",
    # === UTI ===
    "pelvic pain": "pelvic pain",
    "pain in lower abdomen": "pelvic pain",
    # === Meningitis ===
    "stiff neck": "stiff neck",
    "neck stiffness": "stiff neck",
    "shingo ngumu": "stiff neck",
    # === Yellowing ===
    "yellow eyes": "jaundice",
    "yellow skin": "jaundice",
    "yellowish skin": "jaundice",
    "jaundice": "jaundice",
    "dark urine": "dark urine",
    "brown urine": "dark urine",
    "tea colored urine": "dark urine",
    # === Numbness / tingling ===
    "numbness": "numbness",
    "tingling": "tingling",
    "pins and needles": "numbness",
    # === Misc ===
    "malaise": "malaise",
    "feeling unwell": "malaise",
    "sijisikii vizuri": "malaise",
    "cold hands and feet": "cold hands and feet",
    "cold hands": "cold hands and feet",
    "cold feet": "cold hands and feet",
    "watering from eyes": "watering from eyes",
    "tearing eyes": "watering from eyes",
    "loss of smell": "loss of smell",
    "cant smell": "loss of smell",
    "can't smell": "loss of smell",
    "no smell": "loss of smell",
    "loss of taste": "loss of taste",
    "cant taste": "loss of taste",
    "can't taste": "loss of taste",
    "no taste": "loss of taste",
    "frequent infections": "frequent infections",
    "getting sick often": "frequent infections",
}

# Multi-word phrase patterns (order matters: longer first)
_PHRASE_PATTERNS: List[Tuple[str, str]] = [
    (r"my chest feels tight", "chest tightness"),
    (r"chest feels tight", "chest tightness"),
    (r"hard to breathe", "difficulty breathing"),
    (r"difficulty in breathing", "difficulty breathing"),
    (r"trouble breathing", "difficulty breathing"),
    (r"can't breathe", "difficulty breathing"),
    (r"cannot breathe", "difficulty breathing"),
    (r"severe shortness of breath", "difficulty breathing"),
    (r"throwing up", "vomiting"),
    (r"threw up", "vomiting"),
    (r"very hot body", "high fever"),
    (r"hot body", "fever"),
    (r"burning up", "fever"),
    (r"passing out", "altered consciousness"),
    (r"passed out", "altered consciousness"),
    (r"heart racing", "palpitations"),
    (r"racing heart", "palpitations"),
    (r"heart pounding", "palpitations"),
    (r"pain when peeing", "burning urination"),
    (r"painful urination", "burning urination"),
    (r"burning when peeing", "burning urination"),
    (r"burning while urinating", "burning urination"),
    (r"feeling weak", "weakness"),
    (r"feel weak", "weakness"),
    (r"no energy", "fatigue"),
    (r"low energy", "fatigue"),
    (r"body aches", "muscle pain"),
    (r"body ache", "muscle pain"),
    (r"aching all over", "muscle pain"),
    (r"pain all over", "muscle pain"),
    (r"joints hurt", "joint pain"),
    (r"joint hurting", "joint pain"),
    (r"my back hurts", "back pain"),
    (r"back hurting", "back pain"),
    (r"my head hurts", "headache"),
    (r"splitting headache", "severe headache"),
    (r"sore throat", "sore throat"),
    (r"scratchy throat", "sore throat"),
    (r"throat hurts", "sore throat"),
    (r"stuffy nose", "congestion"),
    (r"blocked nose", "congestion"),
    (r"runny nose", "runny nose"),
    (r"dripping nose", "runny nose"),
    (r"skin rash", "rash"),
    (r"red spots", "red spots"),
    (r"itchy skin", "itchy rash"),
    (r"skin itching", "itchy rash"),
    (r"loss of appetite", "loss of appetite"),
    (r"no appetite", "loss of appetite"),
    (r"not hungry", "loss of appetite"),
    (r"losing weight", "weight loss"),
    (r"weight loss", "weight loss"),
    (r"blood in stool", "bloody stool"),
    (r"bloody stool", "bloody stool"),
    (r"blood in urine", "blood in urine"),
    (r"bloody urine", "blood in urine"),
    (r"blurred vision", "blurred vision"),
    (r"cant see clearly", "blurred vision"),
    (r"can't see clearly", "blurred vision"),
    (r"cloudy vision", "blurred vision"),
    (r"confused", "confusion"),
    (r"cant think straight", "confusion"),
    (r"can't think straight", "confusion"),
    (r"mental fog", "confusion"),
    (r"loss of consciousness", "altered consciousness"),
    (r"knocked out", "altered consciousness"),
    (r"seizure", "seizure"),
    (r"convulsion", "seizure"),
    (r"shivering badly", "chills"),
    (r"night sweats", "night sweats"),
    (r"excessive sweating", "sweating"),
    (r"swollen legs", "swelling"),
    (r"leg swelling", "swelling"),
    (r"stiff neck", "stiff neck"),
    (r"neck stiffness", "stiff neck"),
    (r"yellow eyes", "jaundice"),
    (r"yellow skin", "jaundice"),
    (r"dark urine", "dark urine"),
    (r"brown urine", "dark urine"),
    (r"tea colored urine", "dark urine"),
    (r"fast heart rate", "fast heart rate"),
    (r"rapid heartbeat", "fast heart rate"),
    (r"rapid heart rate", "fast heart rate"),
    (r"loss of balance", "dizziness"),
    (r"loss of smell", "loss of smell"),
    (r"cant smell", "loss of smell"),
    (r"can't smell", "loss of smell"),
    (r"no smell", "loss of smell"),
    (r"loss of taste", "loss of taste"),
    (r"cant taste", "loss of taste"),
    (r"can't taste", "loss of taste"),
    (r"no taste", "loss of taste"),
    (r"foul smell of urine", "foul urine"),
    (r"smelly urine", "foul urine"),
    (r"lack of concentration", "confusion"),
    (r"cant concentrate", "confusion"),
    (r"can't concentrate", "confusion"),
    (r"painful walking", "painful walking"),
    (r"hurts to walk", "painful walking"),
    (r"tired all the time", "fatigue"),
    (r"cold hands and feet", "cold hands and feet"),
    (r"cold hands", "cold hands and feet"),
    (r"cold feet", "cold hands and feet"),
    (r"watering from eyes", "watering from eyes"),
    (r"tearing eyes", "watering from eyes"),
    (r"sensitivity to light", "sensitivity to light"),
    (r"light hurts eyes", "sensitivity to light"),
    (r"slow healing wounds", "slow healing"),
    (r"wounds not healing", "slow healing"),
    (r"pain in lower abdomen", "pelvic pain"),
    (r"getting sick often", "frequent infections"),
    (r"persistent cough", "persistent cough"),
    (r"coughing blood", "bloody phlegm"),
    (r"blood in sputum", "bloody phlegm"),
    (r"severe headache", "severe headache"),
    (r"pain behind eyes", "pain behind eyes"),
    (r"pain behind the eyes", "pain behind eyes"),
    (r"mild headache", "headache"),
    (r"extreme thirst", "excessive thirst"),
    (r"very thirsty", "excessive thirst"),
    (r"dry mouth", "dehydration"),
    (r"running stomach", "diarrhea"),
    (r"kuchoka sana", "fatigue"),
    (r"homakali", "high fever"),
    (r"homa kali", "high fever"),
    (r"joto kali", "high fever"),
    (r"baridi kali", "chills"),
    (r"kutetemeka", "chills"),
    (r"tumbo kuumwa", "abdominal pain"),
    (r"tumbo inaenda", "diarrhea"),
    (r"kukojoa uchungu", "burning urination"),
    (r"kukojoa mara nyingi", "frequent urination"),
    (r"kunywa maji sana", "excessive thirst"),
    (r"shingo ngumu", "stiff neck"),
    (r"sijisikii vizuri", "malaise"),
    (r"sikupendi kula", "loss of appetite"),
    (r"uchovu", "fatigue"),
]

_STOP_WORDS: Set[str] = {
    "i", "have", "had", "has", "am", "is", "are", "was", "were", "be", "been",
    "being", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "among", "my", "your", "his",
    "her", "its", "our", "their", "this", "that", "these", "those", "me", "you",
    "him", "them", "us", "it", "feel", "feeling", "feels", "having", "suffering",
    "experiencing", "also", "plus", "including", "some", "very", "extreme",
    "slight", "minor", "persistent", "ongoing", "sudden", "chronic", "long",
    "term", "recurrent", "worst", "intense", "unbearable", "agonizing",
    "excruciating", "rapid", "onset", "cant", "can", "not", "don", "does",
    "did", "do", "will", "would", "could", "should", "may", "might", "must",
    "shall", "cannot", "couldn", "wouldn", "shouldn", "won", "wasn", "weren",
    "isn", "aren", "hasn", "haven", "hadn", "doesn", "didn", "ain", "mightn",
    "mustn", "needn", "shan", "mild", "moderate", "severe", "badly", "all",
    "time", "days", "day", "weeks", "week", "months", "month", "years", "year",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "since", "ago", "last", "next", "every", "each", "sometimes", "often",
    "usually", "always", "never", "really", "quite", "too", "so", "much",
    "more", "less", "most", "least", "many", "few", "little", "bit",
    "like", "as", "than", "only", "just", "even", "still", "yet", "already",
    "again", "back", "away", "down", "off", "out", "over", "under",
    "here", "there", "where", "when", "why", "how", "what", "who", "which",
    "while", "because", "since", "until", "unless", "although", "though",
    "however", "therefore", "thus", "hence", "otherwise", "instead",
    "me", "myself", "yourself", "himself", "herself", "itself", "ourselves",
    "themselves", "yes", "no", "not", "ok", "okay", "well", "maybe",
    "perhaps", "probably", "definitely", "certainly", "sure", "right",
    "now", "then", "today", "tomorrow", "yesterday", "soon", "later",
    "please", "help", "thanks", "thank", "sorry", "excuse", "pardon",
    "hello", "hi", "hey", "goodbye", "bye", "see", "later",
    # Swahili stop words
    "na", "ni", "ya", "wa", "kwa", "kama", "pia", "sana", "zaidi",
    "hii", "hizi", "huyu", "wao", "sisi", "mimi", "wewe", "yeye",
    "kwamba", "lakini", "ingawa", "hata", "bila", "baada",
    "kabla", "katika", "juu", "chini", "kati", "mbele", "nyuma",
    "hapa", "pale", "wapi", "nini", "nani", "gani", "vipi",
}


# ============================================================
# SECTION 3 — RED FLAG DETECTION
# ============================================================

_RED_FLAGS: Set[str] = {
    "chest pain", "severe chest pain",
    "shortness of breath", "difficulty breathing", "severe shortness of breath",
    "seizure", "convulsion", "fit", "kiharusi",
    "altered consciousness", "unconscious", "unresponsive", "passed out", "passing out",
    "severe bleeding", "bleeding", "bloody stool", "bloody phlegm", "blood in sputum",
    "confusion", "severe confusion", "altered sensorium",
    "severe weakness", "paralysis", "weakness of one body side",
    "slurred speech", "dysarthria",
    "cyanosis", "blue lips", "blue fingers",
    "high fever", "very high fever", "homakali", "homa kali",
    "severe headache", "stiff neck", "shingo ngumu",
    "severe abdominal pain", "severe dehydration",
    "inability to speak", "can't speak", "cannot speak",
    "heart attack", "stroke",
    "anaphylaxis", "allergic reaction",
    "poisoning", "overdose", "trauma",
    "suicide", "suicidal",
}


# ============================================================
# SECTION 4 — NORMALIZATION FUNCTIONS
# ============================================================

def _extract_phrases(text: str) -> Tuple[List[str], List[Tuple[int, int]]]:
    """Extract canonical symptoms from natural-language text using phrase patterns.
    Returns (list of canonical symptoms, list of matched spans)."""
    text_lower = text.lower()
    found = []
    matched_spans = []
    # Sort by phrase length descending so longer matches win
    for pattern, canonical in sorted(_PHRASE_PATTERNS, key=lambda x: len(x[0]), reverse=True):
        for m in re.finditer(pattern, text_lower):
            overlap = False
            for start, end in matched_spans:
                if not (m.end() <= start or m.start() >= end):
                    overlap = True
                    break
            if not overlap:
                matched_spans.append((m.start(), m.end()))
                found.append(canonical)
    return found, matched_spans


def _fuzzy_correct(token: str, valid_set: Set[str], cutoff: float = 0.65) -> Optional[str]:
    """Apply fuzzy matching to correct a single token against valid symptoms."""
    token_lower = token.lower().strip()
    if not token_lower or len(token_lower) < 2:
        return None
    if token_lower in valid_set:
        return token_lower
    matches = get_close_matches(token_lower, valid_set, n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    return None


def normalize_symptoms(symptoms_text: str) -> Tuple[List[str], str]:
    """
    Normalize raw symptom text into canonical symptom names.

    Returns:
        (list_of_canonical_symptoms, cleaned_text_for_display)

    Supports:
    - commas, semicolons, newlines
    - natural language and short phrases
    - sentence-style descriptions
    - multi-word symptom understanding
    - typo-resistant alias mapping
    - Kenyan/local phrasing
    - duplicate removal
    """
    if not symptoms_text or not symptoms_text.strip():
        return [], ""

    # Step 1: Extract multi-word phrases first
    phrase_matches, matched_spans = _extract_phrases(symptoms_text)

    cleaned = []
    seen = set()

    for canonical in phrase_matches:
        key = canonical.lower()
        if key not in seen and canonical:
            seen.add(key)
            cleaned.append(canonical)

    # Step 2: Build remaining text by removing matched phrase spans
    text_lower = symptoms_text.lower()
    remaining = ""
    last = 0
    for start, end in sorted(matched_spans):
        remaining += text_lower[last:start]
        last = end
    remaining += text_lower[last:]

    # Step 3: Tokenize remaining words and try unigram / bigram / trigram matching
    words = re.findall(r"[a-zA-Z_]+", remaining)
    i = 0
    while i < len(words):
        w = words[i].lower()
        if w in _STOP_WORDS or len(w) < 2:
            i += 1
            continue

        # Try trigram
        if i + 2 < len(words):
            tri = w + " " + words[i + 1].lower() + " " + words[i + 2].lower()
            if tri in _SYMPTOM_ALIASES:
                cn = _SYMPTOM_ALIASES[tri]
                k = cn.lower()
                if k not in seen:
                    seen.add(k)
                    cleaned.append(cn)
                i += 3
                continue

        # Try bigram
        if i + 1 < len(words):
            bi = w + " " + words[i + 1].lower()
            if bi in _SYMPTOM_ALIASES:
                cn = _SYMPTOM_ALIASES[bi]
                k = cn.lower()
                if k not in seen:
                    seen.add(k)
                    cleaned.append(cn)
                i += 2
                continue

        # Try unigram alias
        if w in _SYMPTOM_ALIASES:
            cn = _SYMPTOM_ALIASES[w]
            k = cn.lower()
            if k not in seen:
                seen.add(k)
                cleaned.append(cn)
            i += 1
            continue

        # Try fuzzy matching against canonical symptoms
        fuzzy = _fuzzy_correct(w, _CANONICAL_SYMPTOMS, cutoff=0.65)
        if fuzzy and fuzzy not in seen:
            seen.add(fuzzy)
            cleaned.append(fuzzy)

        i += 1

    # Also try splitting on commas/semicolons/newlines for any missed tokens
    for raw_token in re.split(r"[,;\n]+", symptoms_text):
        raw_token = raw_token.strip().lower()
        if not raw_token or raw_token in _STOP_WORDS or len(raw_token) < 2:
            continue
        if raw_token in _SYMPTOM_ALIASES:
            cn = _SYMPTOM_ALIASES[raw_token]
            if cn.lower() not in seen:
                seen.add(cn.lower())
                cleaned.append(cn)
        elif raw_token in _CANONICAL_SYMPTOMS:
            if raw_token not in seen:
                seen.add(raw_token)
                cleaned.append(raw_token)

    return cleaned, ", ".join(cleaned)


# ============================================================
# SECTION 5 — RULE-BASED WEIGHTED SCORING
# ============================================================

# Implicit symptom mappings: if A is present, also consider B present at reduced weight
_IMPLICIT_MAPPINGS: Dict[str, List[Tuple[str, float]]] = {
    "fever": [("high fever", 0.4)],
    "high fever": [("fever", 0.8)],
    "chills": [("shivering", 0.6)],
    "shivering": [("chills", 0.8)],
    "vomiting": [("nausea", 0.4)],
    "nausea": [("vomiting", 0.2)],
    "diarrhea": [("abdominal pain", 0.2)],
    "cough": [("persistent cough", 0.6)],
    "persistent cough": [("cough", 0.8)],
    "shortness of breath": [("difficulty breathing", 0.6)],
    "difficulty breathing": [("shortness of breath", 0.6)],
    "chest pain": [("chest tightness", 0.4)],
    "chest tightness": [("chest pain", 0.4)],
    "loss of smell": [("loss of taste", 0.4)],
    "loss of taste": [("loss of smell", 0.4)],
    "excessive thirst": [("polydipsia", 0.8)],
    "polydipsia": [("excessive thirst", 0.8)],
    "frequent urination": [("polyuria", 0.8)],
    "polyuria": [("frequent urination", 0.8)],
    "itchy rash": [("rash", 0.6)],
    "rash": [("itchy rash", 0.4), ("red spots", 0.2)],
    "red spots": [("rash", 0.4)],
    "severe headache": [("headache", 0.8)],
    "headache": [("severe headache", 0.2)],
    "altered consciousness": [("confusion", 0.4)],
    "confusion": [("altered consciousness", 0.2)],
}


def _expand_symptom_set(symptoms: List[str]) -> Dict[str, float]:
    """Expand symptom set with implicit mappings, returning symptom -> weight multiplier."""
    result = {}
    for s in symptoms:
        s_lower = s.lower().strip()
        result[s_lower] = 1.0
        if s_lower in _IMPLICIT_MAPPINGS:
            for implied, multiplier in _IMPLICIT_MAPPINGS[s_lower]:
                if implied not in result:
                    result[implied] = multiplier
                else:
                    result[implied] = max(result[implied], multiplier)
    return result


def _score_diseases(symptoms: List[str]) -> List[Tuple[str, float, Dict]]:
    """
    Score each disease based on weighted symptom matching.

    Scoring formula:
        raw_score = matched_weight / realistic_denominator
        This ensures that matching a few strong symptoms gives a high score,
        while requiring most core symptoms for a near-perfect score.

    Returns:
        List of (disease_name, raw_score, match_details) sorted by raw_score descending.
    """
    symptom_map = _expand_symptom_set(symptoms)
    scored = []

    for disease_name, disease_info in _DISEASE_KB.items():
        weights = disease_info["symptom_weights"]
        max_score = _DISEASE_MAX_SCORES[disease_name]

        matched_weight = 0.0
        matched_symptoms = []
        missing_core = []

        for canonical_symptom, weight in weights.items():
            if canonical_symptom in symptom_map:
                # Apply implicit mapping multiplier
                multiplier = symptom_map[canonical_symptom]
                matched_weight += weight * multiplier
                matched_symptoms.append(canonical_symptom)
            elif weight >= 4:
                missing_core.append(canonical_symptom)

        # Use a realistic denominator: sum of top 8 weighted symptoms
        # This ensures that matching the most important symptoms yields high scores
        # without requiring every single minor symptom
        sorted_weights = sorted(weights.values(), reverse=True)
        realistic_max = sum(sorted_weights[:8])
        denominator = max(18, realistic_max)
        raw_score = min(1.0, matched_weight / denominator)

        # Bonus: if >50% of core symptoms (weight>=4) are matched, boost
        core_symptoms = [s for s, w in weights.items() if w >= 4]
        matched_core = [s for s in matched_symptoms if weights[s] >= 4]
        if core_symptoms and len(matched_core) / len(core_symptoms) >= 0.5:
            raw_score = min(1.0, raw_score * 1.10)

        # Extra bonus: if ALL core symptoms matched, strong boost
        if core_symptoms and len(matched_core) == len(core_symptoms):
            raw_score = min(1.0, raw_score * 1.15)

        scored.append((
            disease_name,
            raw_score,
            {
                "matched_weight": matched_weight,
                "max_score": max_score,
                "matched_symptoms": matched_symptoms,
                "missing_core": missing_core,
                "matched_core_count": len(matched_core),
                "total_core_count": len(core_symptoms),
            }
        ))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# ============================================================
# SECTION 6 — CONFIDENCE CALIBRATION
# ============================================================

def _calibrate_confidence(
    scored: List[Tuple[str, float, Dict]],
    symptoms: List[str],
    has_red_flag: bool,
) -> List[Dict]:
    """
    Calibrate raw scores into clinically believable confidence values.

    Rules:
    - Cap top confidence based on symptom count and red flags
    - Penalize missing core symptoms (but less if many core symptoms ARE matched)
    - Ensure top-3 are distinguishable
    - Never exceed 0.92
    """
    if not scored:
        return []

    num_symptoms = len(symptoms)
    calibrated = []

    for idx, (disease, raw_score, details) in enumerate(scored):
        confidence = raw_score

        # Penalty: very few symptoms = lower confidence ceiling
        if num_symptoms <= 1:
            confidence -= 0.12
        elif num_symptoms <= 2:
            confidence -= 0.06
        elif num_symptoms <= 3:
            confidence -= 0.02

        # Penalty: red flags make us more conservative
        if has_red_flag:
            confidence -= 0.03

        # Penalty: missing core symptoms (weight >= 4)
        # But reduce penalty if many core symptoms ARE matched
        core_ratio = details["matched_core_count"] / max(1, details["total_core_count"])
        missing_core_penalty = len(details["missing_core"]) * 0.015
        if core_ratio >= 0.75:
            missing_core_penalty *= 0.2  # Strongly reduce penalty if most core symptoms matched
        elif core_ratio >= 0.5:
            missing_core_penalty *= 0.5
        confidence -= missing_core_penalty

        # Penalty: if no core symptoms matched at all
        if details["matched_core_count"] == 0 and details["total_core_count"] > 0:
            confidence -= 0.10

        # Floor and cap
        confidence = max(0.05, min(0.92, confidence))

        calibrated.append({
            "condition": disease,
            "confidence": round(confidence, 4),
            "raw_score": round(raw_score, 4),
            "details": details,
        })

    # Sort by calibrated confidence
    calibrated.sort(key=lambda x: x["confidence"], reverse=True)

    # Ensure meaningful separation between top-3
    if len(calibrated) >= 2:
        gap = calibrated[0]["confidence"] - calibrated[1]["confidence"]
        if gap < 0.10 and calibrated[0]["confidence"] > 0.35:
            calibrated[1]["confidence"] = round(
                max(0.08, calibrated[1]["confidence"] - 0.08), 4
            )

    if len(calibrated) >= 3:
        gap = calibrated[1]["confidence"] - calibrated[2]["confidence"]
        if gap < 0.06 and calibrated[1]["confidence"] > 0.20:
            calibrated[2]["confidence"] = round(
                max(0.05, calibrated[2]["confidence"] - 0.06), 4
            )

    # Re-sort after separation adjustments
    calibrated.sort(key=lambda x: x["confidence"], reverse=True)

    # Do NOT normalize top-3 sum to 1.0 — that destroys clinical realism.
    # Instead, just ensure no individual confidence exceeds 0.92.
    for p in calibrated:
        p["confidence"] = round(min(0.92, p["confidence"]), 4)

    return calibrated


# ============================================================
# SECTION 7 — RED FLAG DETECTION
# ============================================================

def detect_red_flags(symptoms_text: str, symptoms: List[str]) -> Tuple[bool, List[str]]:
    """
    Detect high-risk / emergency symptoms in the input.

    Returns:
        (has_red_flag, list_of_detected_flags)
    """
    text_lower = symptoms_text.lower()
    detected = []

    # Check raw text
    for flag in _RED_FLAGS:
        if flag in text_lower:
            detected.append(flag)

    # Check normalized symptoms
    symptom_set = set(s.lower() for s in symptoms)
    for flag in _RED_FLAGS:
        if flag in symptom_set and flag not in detected:
            detected.append(flag)

    # Special combination red flags
    if "fever" in symptom_set and "stiff neck" in symptom_set and "confusion" in symptom_set:
        combo = "meningitis red flag (fever + stiff neck + confusion)"
        if combo not in detected:
            detected.append(combo)

    if "chest pain" in symptom_set and "shortness of breath" in symptom_set:
        combo = "cardiac red flag (chest pain + shortness of breath)"
        if combo not in detected:
            detected.append(combo)

    if "fever" in symptom_set and "rash" in symptom_set and "bleeding" in symptom_set:
        combo = "dengue red flag (fever + rash + bleeding)"
        if combo not in detected:
            detected.append(combo)

    return len(detected) > 0, detected


# ============================================================
# SECTION 8 — INVALID INPUT DETECTION
# ============================================================

def _is_invalid_input(symptoms: List[str], top_raw_score: float) -> Tuple[bool, str]:
    """
    Determine if the input is too vague, nonsense, or unrelated to produce a valid prediction.

    Returns:
        (is_invalid, reason_message)
    """
    if not symptoms:
        return True, "No valid symptoms recognized. Please enter valid medical symptoms."

    if len(symptoms) == 0:
        return True, "No valid symptoms recognized. Please describe your symptoms in more detail."

    # If the best disease match is extremely weak, reject
    if top_raw_score < 0.15:
        return True, "Unable to confidently determine a condition from the provided symptoms. Please describe your symptoms with more detail or consult a doctor directly."

    return False, ""


# ============================================================
# SECTION 9 — CLINICAL INSIGHTS
# ============================================================

def get_disease_info(condition: str) -> Dict:
    """Get clinical information for a predicted condition."""
    condition_key = condition.strip()
    if condition_key in _DISEASE_KB:
        info = _DISEASE_KB[condition_key]
        return {
            "severity": info["severity"],
            "recommended_tests": info["recommended_tests"],
            "clinical_insight": info["clinical_insight"],
            "category": info["category"],
        }
    return {
        "severity": "MEDIUM",
        "recommended_tests": ["Complete Blood Count (CBC)", "Basic metabolic panel", "Relevant imaging based on clinical findings"],
        "clinical_insight": "Based on the reported symptoms, further clinical evaluation is recommended.",
        "category": "general",
    }


def generate_urgency_message(severity: str, has_red_flag: bool, condition: str) -> str:
    """Generate an urgency message based on severity and red flags."""
    if has_red_flag:
        return (
            "URGENT: Potentially life-threatening symptoms detected. "
            "Seek emergency medical care or call emergency services immediately. "
            "Do not wait for symptoms to worsen."
        )
    if severity == "HIGH":
        return (
            f"Your symptoms suggest a potentially serious condition ({condition}). "
            "Seek medical evaluation within 24 hours. "
            "If symptoms worsen, go to the nearest emergency department."
        )
    if severity == "MEDIUM":
        return (
            "Schedule an appointment at the clinic within 24–48 hours. "
            "Seek urgent care sooner if symptoms worsen significantly or if new red-flag symptoms develop."
        )
    return (
        "Monitor symptoms at home. Schedule a routine clinic visit within the next week "
        "if symptoms persist or interfere with daily activities."
    )


def generate_ai_advice(condition: str, severity: str, symptoms: List[str]) -> str:
    """Generate practical AI advice for the patient."""
    if severity == "HIGH":
        return (
            f"This presentation may indicate {condition}, which can be serious. "
            "Please follow the recommended steps closely and seek immediate in-person evaluation if symptoms worsen or red-flag features develop. "
            "Stay hydrated and rest while arranging care."
        )
    elif severity == "MEDIUM":
        return (
            f"Your symptoms are consistent with {condition}. "
            "Monitor your symptoms closely. Rest, stay hydrated, and follow the recommended care plan. "
            "Contact a clinician if symptoms do not improve within 24–48 hours or if new symptoms appear."
        )
    return (
        f"Your symptoms appear mild and may be related to {condition}. "
        "Focus on rest, hydration, and self-care. Schedule a routine follow-up if symptoms persist beyond a few days."
    )


# ============================================================
# SECTION 10 — ML FALLBACK (OPTIONAL)
# ============================================================

def _ml_fallback_predict(symptoms_text: str) -> Optional[List[Dict]]:
    """
    Optional fallback to the old RandomForest model.
    Returns ML predictions or None if model unavailable.
    """
    try:
        from ..symptom_model import predict_topk as ml_predict_topk
        result = ml_predict_topk(symptoms_text)
        if "error" in result:
            return None
        return result.get("predictions", [])
    except Exception as e:
        logger.debug(f"ML fallback unavailable: {e}")
        return None


# ============================================================
# SECTION 11 — MAIN PREDICTION ENTRY POINT
# ============================================================

def predict_topk(
    symptoms_text: str,
    k: int = 3,
    confidence_threshold: float = 0.25,
    use_ml_fallback: bool = True,
) -> Dict:
    """
    Predict top-k diseases from symptoms using the hybrid clinical engine.

    This is the PRIMARY prediction function. It uses rule-based weighted symptom
    scoring as the main predictor, with optional ML fallback for edge cases.

    Args:
        symptoms_text: Raw symptom text from user
        k: Number of top predictions to return
        confidence_threshold: Minimum confidence for "low_confidence" flag
        use_ml_fallback: Whether to blend with ML model predictions

    Returns:
        Dictionary with:
        - predicted_condition: str
        - confidence_score: float
        - top_3_predictions: list of {condition, confidence}
        - severity: str
        - urgency_message: str
        - recommended_tests: list of str
        - red_flag: bool
        - detected_red_flags: list of str
        - cleaned_symptoms: list of str
        - match_quality: str
        - clinical_insight: str
        - ai_advice: str
        - low_confidence: bool
        - error: str or None
    """
    logger.info(f"Clinical engine prediction request: '{symptoms_text}'")

    if not symptoms_text or not symptoms_text.strip():
        return {
            "predicted_condition": None,
            "confidence_score": 0.0,
            "top_3_predictions": [],
            "severity": "LOW",
            "urgency_message": "Please describe your symptoms to receive a prediction.",
            "recommended_tests": [],
            "red_flag": False,
            "detected_red_flags": [],
            "cleaned_symptoms": [],
            "match_quality": "Low Match",
            "clinical_insight": "",
            "ai_advice": "",
            "low_confidence": True,
            "error": "Symptoms text cannot be empty.",
        }

    # Step 1: Normalize input
    symptoms, cleaned_text = normalize_symptoms(symptoms_text)

    # Step 2: Detect red flags
    has_red_flag, detected_flags = detect_red_flags(symptoms_text, symptoms)

    # Step 3: Check for invalid input
    raw_scored = _score_diseases(symptoms)
    top_raw_score = raw_scored[0][1] if raw_scored else 0.0

    is_invalid, invalid_reason = _is_invalid_input(symptoms, top_raw_score)
    if is_invalid:
        return {
            "predicted_condition": None,
            "confidence_score": 0.0,
            "top_3_predictions": [],
            "severity": "LOW",
            "urgency_message": "Please provide more detailed symptom information.",
            "recommended_tests": [],
            "red_flag": has_red_flag,
            "detected_red_flags": detected_flags,
            "cleaned_symptoms": symptoms,
            "match_quality": "Low Match",
            "clinical_insight": "",
            "ai_advice": "",
            "low_confidence": True,
            "error": invalid_reason,
        }

    # Step 4: Calibrate confidence scores
    calibrated = _calibrate_confidence(raw_scored, symptoms, has_red_flag)

    # Step 5: Optional ML fallback blending
    if use_ml_fallback and calibrated and calibrated[0]["confidence"] < 0.50:
        ml_preds = _ml_fallback_predict(symptoms_text)
        if ml_preds:
            calibrated = _blend_with_ml(calibrated, ml_preds)

    # Step 6: Build top-k predictions
    top = calibrated[:max(1, k)]
    top_conf = top[0]["confidence"] if top else 0.0
    primary_condition = top[0]["condition"] if top else None

    # Step 7: Determine match quality
    if top_conf >= 0.70:
        match_quality = "High Match"
    elif top_conf >= 0.40:
        match_quality = "Moderate Match"
    else:
        match_quality = "Low Match"

    # Step 8: Get clinical info for primary condition
    disease_info = get_disease_info(primary_condition) if primary_condition else {}
    severity = disease_info.get("severity", "MEDIUM")

    # Override severity if red flags present
    if has_red_flag and severity != "HIGH":
        severity = "HIGH"

    recommended_tests = disease_info.get("recommended_tests", [])
    clinical_insight = disease_info.get("clinical_insight", "")
    urgency_message = generate_urgency_message(severity, has_red_flag, primary_condition or "Unknown")
    ai_advice = generate_ai_advice(primary_condition or "Unknown", severity, symptoms) if primary_condition else ""

    # Build top_3_predictions list
    top_3_predictions = [
        {"condition": p["condition"], "confidence": p["confidence"]} for p in top
    ]

    return {
        "predicted_condition": primary_condition,
        "confidence_score": round(top_conf, 4),
        "top_3_predictions": top_3_predictions,
        "severity": severity,
        "urgency_message": urgency_message,
        "recommended_tests": recommended_tests,
        "red_flag": has_red_flag,
        "detected_red_flags": detected_flags,
        "cleaned_symptoms": symptoms,
        "match_quality": match_quality,
        "clinical_insight": clinical_insight,
        "ai_advice": ai_advice,
        "low_confidence": top_conf < confidence_threshold,
        "error": None,
    }


def _blend_with_ml(
    clinical_preds: List[Dict],
    ml_preds: List[Dict],
    clinical_weight: float = 0.85,
    ml_weight: float = 0.15,
) -> List[Dict]:
    """
    Blend clinical engine predictions with ML predictions.
    Only ML diseases that are in our KB are blended.
    """
    clinical_map = {p["condition"]: p for p in clinical_preds}
    ml_map = {p["condition"]: p for p in ml_preds}

    all_diseases = set(clinical_map.keys()) | set(ml_map.keys())
    blended = []

    for disease in all_diseases:
        c_conf = clinical_map.get(disease, {}).get("confidence", 0.0)
        m_conf = ml_map.get(disease, {}).get("confidence", 0.0)

        # Only blend if disease is in our KB
        if disease in _DISEASE_KB:
            new_conf = (c_conf * clinical_weight) + (m_conf * ml_weight)
        else:
            # For diseases not in KB, heavily discount ML confidence
            new_conf = m_conf * 0.10

        blended.append({
            "condition": disease,
            "confidence": round(min(0.92, new_conf), 4),
            "raw_score": clinical_map.get(disease, {}).get("raw_score", 0.0),
            "details": clinical_map.get(disease, {}).get("details", {}),
        })

    blended.sort(key=lambda x: x["confidence"], reverse=True)
    return blended


def get_model_info() -> Dict:
    """Get information about the clinical prediction engine."""
    return {
        "loaded": True,
        "engine": "Hybrid Clinical Prediction Engine",
        "version": "2.0",
        "num_diseases": len(_DISEASE_KB),
        "num_symptoms": len(_CANONICAL_SYMPTOMS),
        "diseases": list(_DISEASE_KB.keys()),
        "primary_method": "Rule-based weighted symptom scoring",
        "fallback_method": "RandomForest (optional)",
    }
