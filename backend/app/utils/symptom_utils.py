"""Symptom normalization and AI insight generation utilities."""
import re
from typing import List, Dict, Optional

_SYMPTOM_ALIASES = {
    "paininthejoint": "Joint Pain", "jointpain": "Joint Pain", "joint ache": "Joint Pain",
    "stomachache": "Abdominal Pain", "stomach ache": "Abdominal Pain", "stomach pain": "Abdominal Pain",
    "tummy ache": "Abdominal Pain", "belly pain": "Abdominal Pain",
    "backpain": "Back Pain", "back ache": "Back Pain",
    "headpain": "Headache", "head ache": "Headache",
    "chestpain": "Chest Pain", "chest pain": "Chest Pain",
    "musclepain": "Muscle Pain", "muscle ache": "Muscle Pain",
    "sorethroat": "Sore Throat", "sore throat": "Sore Throat",
    "feverish": "Fever", "high temp": "Fever", "temperature": "Fever",
    "coughing": "Cough", "nauseous": "Nausea", "feel sick": "Nausea",
    "throwing up": "Vomiting", "puking": "Vomiting", "throw up": "Vomiting",
    "diarrhoea": "Diarrhea", "loose stools": "Diarrhea",
    "runnynose": "Runny Nose", "runny nose": "Runny Nose",
    "blockednose": "Nasal Congestion", "stuffy nose": "Nasal Congestion",
    "shortnessofbreath": "Shortness of Breath", "short of breath": "Shortness of Breath",
    "cant breathe": "Shortness of Breath", "difficulty breathing": "Shortness of Breath",
    "dizzy": "Dizziness", "lightheaded": "Dizziness",
    "tired": "Fatigue", "exhausted": "Fatigue", "no energy": "Fatigue",
    "chills": "Chills", "shivering": "Chills",
    "sweating": "Sweating", "sweats": "Sweating",
    "rash": "Skin Rash", "skin rash": "Skin Rash",
    "itching": "Itching", "itchy": "Itching",
    "swelling": "Swelling", "swollen": "Swelling",
    "loss of appetite": "Loss of Appetite", "not hungry": "Loss of Appetite",
    "weight loss": "Weight Loss", "losing weight": "Weight Loss",
    "blood in stool": "Blood in Stool", "bloody stool": "Blood in Stool",
    "blood in urine": "Blood in Urine", "bloody urine": "Blood in Urine",
    "blurred vision": "Blurred Vision", "cant see clearly": "Blurred Vision",
    "confusion": "Confusion", "disoriented": "Confusion",
    "seizure": "Seizure", "convulsion": "Seizure",
    "fainting": "Fainting", "passed out": "Fainting",
    "unconscious": "Unconsciousness",
    "palpitations": "Palpitations", "racing heart": "Palpitations", "heart racing": "Palpitations",
}

_CONDITION_INSIGHTS: Dict[str, Dict] = {
    "malaria": {"insight": "Malaria is a mosquito-borne disease caused by Plasmodium parasites.", "risk_level": "HIGH", "suggested_steps": "Immediate blood test. Start antimalarial therapy if confirmed."},
    "typhoid": {"insight": "Typhoid fever is a bacterial infection caused by Salmonella typhi.", "risk_level": "HIGH", "suggested_steps": "Blood culture or Widal test. Start antibiotic therapy."},
    "dengue": {"insight": "Dengue is a viral infection transmitted by Aedes mosquitoes.", "risk_level": "HIGH", "suggested_steps": "NS1 antigen test. Monitor platelet count and hematocrit."},
    "tuberculosis": {"insight": "Tuberculosis is a bacterial infection primarily affecting the lungs.", "risk_level": "HIGH", "suggested_steps": "Sputum AFB smear and culture, chest X-ray."},
    "pneumonia": {"insight": "Pneumonia is an infection that inflames air sacs in the lungs.", "risk_level": "HIGH", "suggested_steps": "Chest X-ray, CBC, sputum culture. Start empiric antibiotics."},
    "asthma": {"insight": "Asthma is a chronic inflammatory disease of the airways.", "risk_level": "MEDIUM", "suggested_steps": "Peak expiratory flow measurement, spirometry."},
    "diabetes": {"insight": "Diabetes mellitus is a metabolic disorder with high blood sugar levels.", "risk_level": "MEDIUM", "suggested_steps": "Fasting blood glucose, HbA1c test."},
    "hypertension": {"insight": "Hypertension is chronically elevated blood pressure.", "risk_level": "MEDIUM", "suggested_steps": "Multiple BP readings, ECG, renal function tests."},
    "heart disease": {"insight": "Heart disease includes coronary artery disease and heart failure.", "risk_level": "HIGH", "suggested_steps": "ECG, troponin levels, echocardiogram."},
    "migraine": {"insight": "Migraine is a neurological condition with recurrent severe headaches.", "risk_level": "MEDIUM", "suggested_steps": "Rule out secondary causes. Acute treatment with triptans."},
    "gerd": {"insight": "GERD occurs when stomach acid flows back into the esophagus.", "risk_level": "LOW", "suggested_steps": "Trial of PPI therapy, lifestyle modifications."},
    "depression": {"insight": "Depression is a mood disorder causing persistent sadness.", "risk_level": "MEDIUM", "suggested_steps": "PHQ-9 screening. Psychotherapy and/or SSRIs."},
    "anxiety": {"insight": "Anxiety disorders involve excessive worry and fear.", "risk_level": "MEDIUM", "suggested_steps": "GAD-7 screening. CBT as first-line treatment."},
    "common cold": {"insight": "The common cold is a viral infection of the upper respiratory tract.", "risk_level": "LOW", "suggested_steps": "Supportive care: rest, hydration."},
    "flu": {"insight": "Influenza is a viral respiratory infection.", "risk_level": "MEDIUM", "suggested_steps": "Rapid influenza test. Antiviral therapy for high-risk patients."},
    "covid": {"insight": "COVID-19 is caused by SARS-CoV-2 virus.", "risk_level": "MEDIUM", "suggested_steps": "RT-PCR or rapid antigen test. Monitor oxygen saturation."},
    "arthritis": {"insight": "Arthritis is inflammation of joints causing pain and stiffness.", "risk_level": "MEDIUM", "suggested_steps": "X-rays, RF and anti-CCP antibodies."},
    "skin rash": {"insight": "Skin rash can result from infections, allergies, or autoimmune conditions.", "risk_level": "LOW", "suggested_steps": "Visual examination. Topical corticosteroids."},
    "allergic reaction": {"insight": "Allergic reactions range from mild skin symptoms to life-threatening anaphylaxis.", "risk_level": "HIGH", "suggested_steps": "Assess airway. Epinephrine for anaphylaxis."},
    "gastroenteritis": {"insight": "Gastroenteritis is inflammation of the stomach and intestines.", "risk_level": "MEDIUM", "suggested_steps": "Oral rehydration therapy. Stool culture if severe."},
    "urinary tract infection": {"insight": "UTI is an infection in the urinary system.", "risk_level": "MEDIUM", "suggested_steps": "Urine dipstick and culture. Start empiric antibiotics."},
    "anemia": {"insight": "Anemia is a condition with inadequate healthy red blood cells.", "risk_level": "MEDIUM", "suggested_steps": "CBC, ferritin, B12, folate levels."},
}


def _normalize_token(token: str) -> str:
    token = token.lower().strip().replace("_", " ").replace("-", " ")
    token = re.sub(r"\s+", " ", token)
    return token


def normalize_symptoms(symptoms_text: str) -> str:
    if not symptoms_text:
        return ""
    raw_tokens = re.split(r"[,;\n]+", symptoms_text)
    cleaned = []
    seen = set()
    for token in raw_tokens:
        token = token.strip()
        if not token or len(token) < 2:
            continue
        normalized = _normalize_token(token)
        if normalized in _SYMPTOM_ALIASES:
            clean_name = _SYMPTOM_ALIASES[normalized]
        else:
            clean_name = " ".join(word.capitalize() for word in normalized.split())
        key = clean_name.lower()
        if key not in seen and clean_name:
            seen.add(key)
            cleaned.append(clean_name)
    return ", ".join(cleaned)


def symptoms_to_chips(symptoms_text: str) -> List[str]:
    clean = normalize_symptoms(symptoms_text)
    if not clean:
        return []
    return [s.strip() for s in clean.split(",") if s.strip()]


def generate_ai_insight(predicted_condition: Optional[str], symptoms: str, priority: str) -> Dict:
    condition = (predicted_condition or "").lower().strip()
    if condition in _CONDITION_INSIGHTS:
        data = _CONDITION_INSIGHTS[condition].copy()
        data["risk_level"] = priority if priority in ("LOW", "MEDIUM", "HIGH") else data["risk_level"]
        return data
    for key, data in _CONDITION_INSIGHTS.items():
        if key in condition or condition in key:
            result = data.copy()
            result["risk_level"] = priority if priority in ("LOW", "MEDIUM", "HIGH") else result["risk_level"]
            return result
    return {
        "insight": f"Based on the reported symptoms ({symptoms}), further clinical evaluation is recommended.",
        "risk_level": priority if priority in ("LOW", "MEDIUM", "HIGH") else "MEDIUM",
        "suggested_steps": "Complete physical examination, relevant laboratory tests, and specialist referral.",
    }


def generate_acknowledgement(symptoms: str, condition: Optional[str]) -> str:
    chips = symptoms_to_chips(symptoms)
    if chips:
        return f"Thank you for reaching out. I have reviewed your reported symptoms ({', '.join(chips)})."
    return "Thank you for reaching out. I have reviewed your reported symptoms."


def generate_advice(condition: Optional[str], priority: str) -> str:
    if priority == "HIGH":
        return "This condition requires prompt medical attention. Please follow the recommended steps closely and seek immediate care if symptoms worsen."
    elif priority == "MEDIUM":
        return "Monitor your symptoms closely. Rest, stay hydrated, and follow the recommended care plan. Contact us if symptoms do not improve within 24-48 hours."
    return "Your symptoms appear mild. Focus on rest, hydration, and self-care. Schedule a follow-up if symptoms persist beyond a few days."


def generate_suggested_tests(condition: Optional[str]) -> str:
    condition_lower = (condition or "").lower()
    test_map = {
        "malaria": "- Thick and thin blood smear\n- Rapid diagnostic test (RDT)\n- Complete Blood Count (CBC)",
        "typhoid": "- Blood culture\n- Widal test\n- CBC with differential",
        "dengue": "- NS1 antigen test\n- Dengue IgM/IgG serology\n- CBC (platelet count)",
        "tuberculosis": "- Sputum AFB smear and culture\n- Chest X-ray\n- GeneXpert MTB/RIF",
        "pneumonia": "- Chest X-ray\n- CBC\n- Sputum culture\n- Blood culture",
        "asthma": "- Peak expiratory flow\n- Spirometry\n- Chest X-ray (if first episode)",
        "diabetes": "- Fasting blood glucose\n- HbA1c\n- Lipid profile\n- Renal function tests",
        "hypertension": "- Multiple BP readings\n- ECG\n- Renal function tests\n- Lipid profile",
        "heart disease": "- ECG\n- Troponin levels\n- Echocardiogram\n- Stress test",
        "migraine": "- Clinical evaluation\n- CT/MRI brain (if red flags)\n- Vision assessment",
        "gerd": "- Trial of PPI therapy\n- Upper GI endoscopy (if alarm symptoms)",
        "depression": "- PHQ-9 questionnaire\n- Thyroid function tests\n- CBC",
        "anxiety": "- GAD-7 questionnaire\n- Thyroid function tests\n- CBC",
        "common cold": "- Clinical diagnosis\n- Rapid strep test (if sore throat)",
        "flu": "- Rapid influenza test\n- CBC\n- Chest X-ray (if pneumonia suspected)",
        "covid": "- RT-PCR or rapid antigen test\n- CBC\n- CRP\n- Chest X-ray",
        "arthritis": "- X-rays of affected joints\n- RF and anti-CCP antibodies\n- ESR and CRP",
        "skin rash": "- Visual examination\n- Skin scraping (if fungal)\n- Patch testing",
        "allergic": "- Clinical assessment\n- Specific IgE testing\n- Skin prick test",
        "gastroenteritis": "- Stool culture (if severe)\n- CBC\n- Electrolyte panel",
        "urinary": "- Urinalysis and culture\n- CBC\n- Renal function tests",
        "anemia": "- CBC with differential\n- Ferritin\n- Vitamin B12 and folate",
    }
    for key, tests in test_map.items():
        if key in condition_lower:
            return tests
    return "- Complete Blood Count (CBC)\n- Basic metabolic panel\n- Relevant imaging based on clinical findings"


def generate_urgency(priority: str) -> str:
    if priority == "HIGH":
        return "URGENT: Visit the emergency department or call emergency services immediately if you experience difficulty breathing, chest pain, severe weakness, or confusion."
    elif priority == "MEDIUM":
        return "Schedule an appointment at the clinic within 24-48 hours. Seek urgent care sooner if symptoms worsen significantly."
    return "Monitor symptoms at home. Schedule a routine clinic visit within the next week if symptoms persist."
