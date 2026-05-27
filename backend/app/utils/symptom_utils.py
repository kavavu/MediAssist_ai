"""Symptom normalization and AI insight generation utilities."""
import re
from typing import List, Dict, Optional, Tuple

# ============================================================
# SECTION 1 — EXPANDED SYMPTOM NORMALIZATION
# ============================================================

# NOTE: The primary normalization now lives in backend/app/ml/clinical/engine.py.
# This file retains aliases for non-clinical uses (consultation service, etc.)
# and provides AI insight generation.

_SYMPTOM_ALIASES = {
    # Pain-related
    "paininthejoint": "Joint Pain", "jointpain": "Joint Pain", "joint ache": "Joint Pain",
    "joint hurting": "Joint Pain", "joints hurt": "Joint Pain", "joint discomfort": "Joint Pain",
    "stomachache": "Abdominal Pain", "stomach ache": "Abdominal Pain", "stomach pain": "Abdominal Pain",
    "tummy ache": "Abdominal Pain", "belly pain": "Abdominal Pain", "tummy pain": "Abdominal Pain",
    "pain in stomach": "Abdominal Pain", "pain in abdomen": "Abdominal Pain",
    "tumbo kuumwa": "Abdominal Pain",
    "backpain": "Back Pain", "back ache": "Back Pain", "back hurting": "Back Pain",
    "my back hurts": "Back Pain", "pain in back": "Back Pain",
    "headpain": "Headache", "head ache": "Headache", "my head hurts": "Headache",
    "pain in head": "Headache", "migraine": "Headache", "splitting headache": "Headache",
    "chestpain": "Chest Pain", "chest pain": "Chest Pain", "chest tightness": "Chest Pain",
    "my chest feels tight": "Chest Pain", "tight chest": "Chest Pain", "chest discomfort": "Chest Pain",
    "pain in chest": "Chest Pain",
    "musclepain": "Muscle Pain", "muscle ache": "Muscle Pain", "muscles hurt": "Muscle Pain",
    "body pain": "Muscle Pain", "body ache": "Muscle Pain", "body aches": "Muscle Pain",
    "pain all over": "Muscle Pain", "aching body": "Muscle Pain",
    "sorethroat": "Sore Throat", "sore throat": "Sore Throat", "throat pain": "Sore Throat",
    "painful throat": "Sore Throat", "scratchy throat": "Sore Throat",
    "throat hurts": "Sore Throat", "hurting throat": "Sore Throat",
    # Fever / temperature
    "feverish": "Fever", "high temp": "Fever", "temperature": "Fever",
    "very hot body": "Fever", "running temperature": "Fever", "feeling hot": "Fever",
    "burning up": "Fever", "hot body": "Fever", "febrile": "Fever",
    "homakali": "High Fever", "homa kali": "High Fever", "joto kali": "High Fever",
    # Respiratory
    "coughing": "Cough", "cough": "Cough", "persistent cough": "Cough",
    "dry cough": "Cough", "wet cough": "Cough", "hacking cough": "Cough",
    # Breathing
    "shortnessofbreath": "Shortness of Breath", "short of breath": "Shortness of Breath",
    "cant breathe": "Shortness of Breath", "difficulty breathing": "Shortness of Breath",
    "hard to breathe": "Shortness of Breath", "breathlessness": "Shortness of Breath",
    "labored breathing": "Shortness of Breath", "gasping": "Shortness of Breath",
    "can't breathe": "Shortness of Breath", "cannot breathe": "Shortness of Breath",
    "trouble breathing": "Shortness of Breath", "difficulty in breathing": "Shortness of Breath",
    # GI
    "nauseous": "Nausea", "feel sick": "Nausea", "feeling sick": "Nausea",
    "queasy": "Nausea", "nauseated": "Nausea",
    "throwing up": "Vomiting", "puking": "Vomiting", "throw up": "Vomiting",
    "vomitted": "Vomiting", "vomitting": "Vomiting", "threw up": "Vomiting",
    "diarrhoea": "Diarrhea", "loose stools": "Diarrhea", "watery stool": "Diarrhea",
    "loose motion": "Diarrhea", "frequent stools": "Diarrhea",
    "running stomach": "Diarrhea", "tumbo inaenda": "Diarrhea",
    # ENT
    "runnynose": "Runny Nose", "runny nose": "Runny Nose", "dripping nose": "Runny Nose",
    "blockednose": "Nasal Congestion", "stuffy nose": "Nasal Congestion",
    "blocked nose": "Nasal Congestion", "nasal blockage": "Nasal Congestion",
    "congested nose": "Nasal Congestion",
    # Neuro / general
    "dizzy": "Dizziness", "lightheaded": "Dizziness", "spinning head": "Dizziness",
    "feeling faint": "Dizziness", "woozy": "Dizziness",
    "tired": "Fatigue", "exhausted": "Fatigue", "no energy": "Fatigue",
    "feeling weak": "Fatigue", "weakness": "Fatigue", "lethargic": "Fatigue",
    "low energy": "Fatigue", "worn out": "Fatigue", "drained": "Fatigue",
    "tired all the time": "Fatigue",
    "kuchoka": "Fatigue", "kuchoka sana": "Fatigue", "uchovu": "Fatigue",
    # Chills / sweating
    "chills": "Chills", "shivering": "Chills", "rigors": "Chills",
    "shivering badly": "Chills",
    "sweating": "Sweating", "sweats": "Sweating", "excessive sweating": "Sweating",
    "night sweats": "Sweating",
    "baridi kali": "Chills", "kutetemeka": "Chills",
    # Skin
    "rash": "Skin Rash", "skin rash": "Skin Rash", "red spots": "Skin Rash",
    "spots on skin": "Skin Rash", "skin eruption": "Skin Rash",
    "itching": "Itching", "itchy": "Itching", "pruritus": "Itching",
    "itchy skin": "Itching", "skin itching": "Itching",
    # Swelling / edema
    "swelling": "Swelling", "swollen": "Swelling", "puffy": "Swelling",
    "edema": "Swelling", "bloated": "Swelling",
    # Appetite / weight
    "loss of appetite": "Loss of Appetite", "not hungry": "Loss of Appetite",
    "no appetite": "Loss of Appetite", "appetite loss": "Loss of Appetite",
    "sikupendi kula": "Loss of Appetite",
    "weight loss": "Weight Loss", "losing weight": "Weight Loss",
    "unintended weight loss": "Weight Loss",
    # Bleeding / excretion
    "blood in stool": "Blood in Stool", "bloody stool": "Blood in Stool",
    "blood in urine": "Blood in Urine", "bloody urine": "Blood in Urine",
    "pain when peeing": "Burning Micturition", "burning urination": "Burning Micturition",
    "painful urination": "Burning Micturition", "burning when peeing": "Burning Micturition",
    "burning while urinating": "Burning Micturition",
    "kukojoa uchungu": "Burning Micturition",
    "kukojoa mara nyingi": "Frequent Urination",
    # Vision / neuro
    "blurred vision": "Blurred Vision", "cant see clearly": "Blurred Vision",
    "can't see clearly": "Blurred Vision", "cloudy vision": "Blurred Vision",
    "fuzzy vision": "Blurred Vision",
    "confusion": "Confusion", "disoriented": "Confusion", "confused": "Confusion",
    "cant think straight": "Confusion", "can't think straight": "Confusion",
    "mental fog": "Confusion",
    # Consciousness
    "seizure": "Seizure", "convulsion": "Seizure", "fit": "Seizure",
    "kiharusi": "Seizure",
    "debe": "Abdominal Pain",
    "tumbo kubwa": "Distention of Abdomen",
    "tumbo kuchafua": "Diarrhea",
    "tumbo kuhara": "Diarrhea",
    "kichefuchefu": "Nausea",
    "kutapika": "Vomiting",
    "tapika": "Vomiting",
    "kikohozi": "Cough",
    "kikohozi kikali": "Persistent Cough",
    "pumzi kukata": "Shortness of Breath",
    "pumzi kushindwa": "Shortness of Breath",
    "kichwa kuumwa": "Headache",
    "kichwa kumaumivu": "Headache",
    "kichwa kupiga": "Headache",
    "mgongo kuumwa": "Back Pain",
    "kifua kuumwa": "Chest Pain",
    "kifua kukaza": "Chest Pain",
    "mshipa kuumwa": "Muscle Pain",
    "viungo kuumwa": "Joint Pain",
    "koo kuumwa": "Sore Throat",
    "pua kujaa maji": "Runny Nose",
    "pua kufungika": "Nasal Congestion",
    "jicho kuharibika": "Blurred Vision",
    "jicho kudhoofu": "Blurred Vision",
    "mwili kulegea": "Fatigue",
    "mwili kudhoofu": "Fatigue",
    "usingizi kukosa": "Insomnia",
    "usingizi kushindwa": "Insomnia",
    "moyo kupiga kasi": "Palpitations",
    "moyo kupiga mno": "Palpitations",
    "ngozi kujaa madoa": "Skin Rash",
    "ngozi kutu": "Itching",
    "kutokwa na jasho": "Sweating",
    "jasho kupita kiasi": "Sweating",
    "kupoteza uzito": "Weight Loss",
    "kupata uzito": "Weight Gain",
    "njaa kupita kiasi": "Excessive Hunger",
    "njaa sana": "Excessive Hunger",
    "kukojoa damu": "Blood in Urine",
    "kunywa maji sana": "Polydipsia",
    "kukojoa mara nyingi": "Frequent Urination",
    "kukojoa uchungu": "Burning Micturition",
    "tumbo kuumwa": "Abdominal Pain",
    "tumbo inaenda": "Diarrhea",
    "homakali": "High Fever",
    "homa kali": "High Fever",
    "joto kali": "High Fever",
    "baridi kali": "Chills",
    "kutetemeka": "Chills",
    "shingo ngumu": "Stiff Neck",
    "sijisikii vizuri": "Malaise",
    "sikupendi kula": "Loss of Appetite",
    "kuchoka": "Fatigue",
    "kuchoka sana": "Fatigue",
    "uchovu": "Fatigue",
    "fainting": "Fainting", "passed out": "Fainting", "passing out": "Fainting",
    "syncope": "Fainting",
    "unconscious": "Unconsciousness", "knocked out": "Unconsciousness",
    "loss of consciousness": "Unconsciousness", "unresponsive": "Unconsciousness",
    # Cardiac
    "palpitations": "Palpitations", "racing heart": "Palpitations",
    "heart racing": "Palpitations", "heart pounding": "Palpitations",
    "skipped beats": "Palpitations", "fluttering heart": "Palpitations",
    # Additional common symptoms
    "sneezing": "Sneezing", "sneeze": "Sneezing",
    "wheezing": "Wheezing", "wheeze": "Wheezing",
    "congestion": "Congestion", "nasal congestion": "Congestion",
    "dehydration": "Dehydration", "dry mouth": "Dehydration", "very thirsty": "Dehydration",
    "yellow eyes": "Yellowing of Eyes", "yellow skin": "Yellowish Skin",
    "jaundice": "Yellowish Skin",
    "stiff neck": "Stiff Neck", "neck stiffness": "Stiff Neck",
    "shingo ngumu": "Stiff Neck",
    "numbness": "Numbness", "tingling": "Numbness", "pins and needles": "Numbness",
    "anxiety": "Anxiety", "worried": "Anxiety", "nervous": "Anxiety",
    "depression": "Depression", "sad": "Depression", "feeling down": "Depression",
    "insomnia": "Insomnia", "cant sleep": "Insomnia", "trouble sleeping": "Insomnia",
    "can't sleep": "Insomnia",
    "constipation": "Constipation", "cant poop": "Constipation",
    "indigestion": "Indigestion", "heartburn": "Indigestion", "acid reflux": "Indigestion",
    "bruising": "Bruising", "bruises easily": "Bruising",
    "bleeding": "Bleeding", "bleeding a lot": "Bleeding",
    "high blood pressure": "Hypertension", "bp high": "Hypertension",
    "low blood pressure": "Low Blood Pressure", "bp low": "Low Blood Pressure",
    "sugar high": "Diabetes", "blood sugar high": "Diabetes",
    "wounds not healing": "Delayed Healing",
    "obesity": "Obesity", "overweight": "Obesity",
    "polyuria": "Polyuria", "peeing a lot": "Polyuria", "frequent urination": "Polyuria",
    "polydipsia": "Polydipsia", "drinking a lot": "Polydipsia", "very thirsty": "Polydipsia",
    "kunywa maji sana": "Polydipsia",
    "pain during bowel movements": "Pain During Bowel Movements",
    "bloody phlegm": "Bloody Phlegm", "blood in sputum": "Bloody Phlegm",
    "sinus pressure": "Sinus Pressure", "sinus pain": "Sinus Pressure",
    "mucoid sputum": "Mucoid Sputum", "mucus": "Mucoid Sputum",
    "rusty sputum": "Rusty Sputum",
    "extra marital contacts": "Extra Marital Contacts",
    "receiving blood transfusion": "Receiving Blood Transfusion",
    "receiving unsterile injections": "Receiving Unsterile Injections",
    "family history": "Family History",
    "history of alcohol consumption": "History of Alcohol Consumption",
    "irritability": "Irritability", "irritable": "Irritability", "easily annoyed": "Irritability",
    "restlessness": "Restlessness", "restless": "Restlessness",
    "redness of eyes": "Redness of Eyes", "bloodshot eyes": "Redness of Eyes",
    "watering from eyes": "Watering from Eyes", "tearing eyes": "Watering from Eyes",
    "acute liver failure": "Acute Liver Failure",
    "stomach bleeding": "Stomach Bleeding", "gi bleed": "Stomach Bleeding",
    "distention of abdomen": "Distention of Abdomen", "bloated abdomen": "Distention of Abdomen",
    "abdominal distension": "Distention of Abdomen",
    "fluid overload": "Fluid Overload",
    "toxic look typhos": "Toxic Look (Typhos)",
    "altered sensorium": "Altered Sensorium",
    "red spot over body": "Red Spots Over Body",
    "small dents in nails": "Small Dents in Nails",
    "inflammatory nails": "Inflammatory Nails",
    "blister": "Blister", "blisters": "Blister",
    "red sore around nose": "Red Sore Around Nose",
    "yellow crust ooze": "Yellow Crust Ooze",
    "slurred speech": "Slurred Speech", "slurring": "Slurred Speech",
    "dysarthria": "Slurred Speech",
    "knee pain": "Knee Pain", "pain in knee": "Knee Pain",
    "hip joint pain": "Hip Joint Pain", "pain in hip": "Hip Joint Pain",
    "neck pain": "Neck Pain", "pain in neck": "Neck Pain",
    "pain in anal region": "Pain in Anal Region", "anal pain": "Pain in Anal Region",
    "cramps": "Cramps", "cramping": "Cramps", "muscle cramps": "Cramps",
    "abnormal menstruation": "Abnormal Menstruation", "irregular periods": "Abnormal Menstruation",
    "continuous sneezing": "Continuous Sneezing", "sneezing a lot": "Continuous Sneezing",
    "shivering": "Shivering",
    "cold hands and feets": "Cold Hands and Feets", "cold hands": "Cold Hands and Feets",
    "cold feet": "Cold Hands and Feets",
    "mood swings": "Mood Swings",
    "weight gain": "Weight Gain", "gaining weight": "Weight Gain",
    "lethargy": "Lethargy",
    "patches in throat": "Patches in Throat", "white patches throat": "Patches in Throat",
    "irregular sugar level": "Irregular Sugar Level",
    "high fever": "High Fever", "very high fever": "High Fever",
    "sunken eyes": "Sunken Eyes",
    "breathlessness": "Breathlessness",
    "headache": "Headache",
    "yellowish skin": "Yellowish Skin",
    "dark urine": "Dark Urine", "brown urine": "Dark Urine", "tea colored urine": "Dark Urine",
    "nausea": "Nausea",
    "loss of appetite": "Loss of Appetite",
    "pain behind the eyes": "Pain Behind the Eyes",
    "back pain": "Back Pain",
    "constipation": "Constipation",
    "abdominal pain": "Abdominal Pain",
    "diarrhoea": "Diarrhoea",
    "mild fever": "Mild Fever",
    "yellow urine": "Yellow Urine",
    "yellowing of eyes": "Yellowing of Eyes",
    "swelling of stomach": "Swelling of Stomach",
    "swelled lymph nodes": "Swelled Lymph Nodes", "swollen lymph nodes": "Swelled Lymph Nodes",
    "malaise": "Malaise", "feeling unwell": "Malaise", "sijisikii vizuri": "Malaise",
    "blurred and distorted vision": "Blurred and Distorted Vision",
    "phlegm": "Phlegm", "mucus in throat": "Phlegm",
    "throat irritation": "Throat Irritation",
    "sinus pressure": "Sinus Pressure",
    "runny nose": "Runny Nose",
    "congestion": "Congestion",
    "chest pain": "Chest Pain",
    "weakness in limbs": "Weakness in Limbs", "limb weakness": "Weakness in Limbs",
    "fast heart rate": "Fast Heart Rate", "rapid heartbeat": "Fast Heart Rate",
    "pain during bowel movements": "Pain During Bowel Movements",
    "pain in anal region": "Pain in Anal Region",
    "bloody stool": "Bloody Stool",
    "irritation in anus": "Irritation in Anus",
    "dizziness": "Dizziness",
    "bruising": "Bruising",
    "obesity": "Obesity",
    "swollen legs": "Swollen Legs", "leg swelling": "Swollen Legs",
    "swollen blood vessels": "Swollen Blood Vessels",
    "puffy face and eyes": "Puffy Face and Eyes",
    "enlarged thyroid": "Enlarged Thyroid", "goiter": "Enlarged Thyroid",
    "brittle nails": "Brittle Nails",
    "swollen extremeties": "Swollen Extremeties",
    "excessive hunger": "Excessive Hunger", "always hungry": "Excessive Hunger",
    "drying and tingling lips": "Drying and Tingling Lips",
    "knee pain": "Knee Pain",
    "hip joint pain": "Hip Joint Pain",
    "muscle weakness": "Muscle Weakness",
    "stiff neck": "Stiff Neck",
    "swelling joints": "Swelling Joints", "swollen joints": "Swelling Joints",
    "movement stiffness": "Movement Stiffness",
    "spinning movements": "Spinning Movements",
    "loss of balance": "Loss of Balance", "unsteady": "Loss of Balance",
    "unsteadiness": "Unsteadiness",
    "weakness of one body side": "Weakness of One Body Side",
    "loss of smell": "Loss of Smell", "cant smell": "Loss of Smell", "no smell": "Loss of Smell",
    "can't smell": "Loss of Smell",
    "bladder discomfort": "Bladder Discomfort",
    "foul smell of urine": "Foul Smell of Urine", "smelly urine": "Foul Smell of Urine",
    "continuous feel of urine": "Continuous Feel of Urine",
    "passage of gases": "Passage of Gases", "gas": "Passage of Gases", "flatulence": "Passage of Gases",
    "internal itching": "Internal Itching",
    "muscle pain": "Muscle Pain",
    "red spots over body": "Red Spots Over Body",
    "belly pain": "Abdominal Pain",
    "abnormal menstruation": "Abnormal Menstruation",
    "dischromic patches": "Dischromic Patches",
    "watering from eyes": "Watering from Eyes",
    "increased appetite": "Increased Appetite",
    "polyuria": "Polyuria",
    "family history": "Family History",
    "mucoid sputum": "Mucoid Sputum",
    "rusty sputum": "Rusty Sputum",
    "blood in sputum": "Bloody Phlegm",
    "lack of concentration": "Lack of Concentration", "cant concentrate": "Lack of Concentration",
    "can't concentrate": "Lack of Concentration",
    "visual disturbances": "Visual Disturbances",
    "receiving blood transfusion": "Receiving Blood Transfusion",
    "receiving unsterile injections": "Receiving Unsterile Injections",
    "coma": "Coma",
    "stomach bleeding": "Stomach Bleeding",
    "distention of abdomen": "Distention of Abdomen",
    "history of alcohol consumption": "History of Alcohol Consumption",
    "blood in sputum": "Bloody Phlegm",
    "prominent veins on calf": "Prominent Veins on Calf",
    "palpitations": "Palpitations",
    "painful walking": "Painful Walking", "hurts to walk": "Painful Walking",
    "pus filled pimples": "Pus Filled Pimples",
    "blackheads": "Blackheads",
    "scurring": "Scurring",
    "skin peeling": "Skin Peeling",
    "silver like dusting": "Silver Like Dusting",
    "small dents in nails": "Small Dents in Nails",
    "inflammatory nails": "Inflammatory Nails",
    "red sore around nose": "Red Sore Around Nose",
    "yellow crust ooze": "Yellow Crust Ooze",
}

# Multi-word phrase patterns that map directly to canonical symptoms
# Order matters: longer / more specific phrases first
_PHRASE_PATTERNS: List[Tuple[str, str]] = [
    (r"my chest feels tight", "Chest Pain"),
    (r"chest feels tight", "Chest Pain"),
    (r"hard to breathe", "Shortness of Breath"),
    (r"difficulty in breathing", "Shortness of Breath"),
    (r"trouble breathing", "Shortness of Breath"),
    (r"can't breathe", "Shortness of Breath"),
    (r"cannot breathe", "Shortness of Breath"),
    (r"throwing up", "Vomiting"),
    (r"threw up", "Vomiting"),
    (r"very hot body", "Fever"),
    (r"hot body", "Fever"),
    (r"burning up", "Fever"),
    (r"passing out", "Fainting"),
    (r"passed out", "Fainting"),
    (r"heart racing", "Palpitations"),
    (r"racing heart", "Palpitations"),
    (r"heart pounding", "Palpitations"),
    (r"pain when peeing", "Burning Micturition"),
    (r"painful urination", "Burning Micturition"),
    (r"burning when peeing", "Burning Micturition"),
    (r"burning while urinating", "Burning Micturition"),
    (r"feeling weak", "Fatigue"),
    (r"feel weak", "Fatigue"),
    (r"no energy", "Fatigue"),
    (r"low energy", "Fatigue"),
    (r"body aches", "Muscle Pain"),
    (r"body ache", "Muscle Pain"),
    (r"aching all over", "Muscle Pain"),
    (r"pain all over", "Muscle Pain"),
    (r"joints hurt", "Joint Pain"),
    (r"joint hurting", "Joint Pain"),
    (r"my back hurts", "Back Pain"),
    (r"back hurting", "Back Pain"),
    (r"my head hurts", "Headache"),
    (r"splitting headache", "Headache"),
    (r"sore throat", "Sore Throat"),
    (r"scratchy throat", "Sore Throat"),
    (r"throat hurts", "Sore Throat"),
    (r"stuffy nose", "Nasal Congestion"),
    (r"blocked nose", "Nasal Congestion"),
    (r"runny nose", "Runny Nose"),
    (r"dripping nose", "Runny Nose"),
    (r"skin rash", "Skin Rash"),
    (r"red spots", "Skin Rash"),
    (r"itchy skin", "Itching"),
    (r"skin itching", "Itching"),
    (r"loss of appetite", "Loss of Appetite"),
    (r"no appetite", "Loss of Appetite"),
    (r"not hungry", "Loss of Appetite"),
    (r"losing weight", "Weight Loss"),
    (r"weight loss", "Weight Loss"),
    (r"blood in stool", "Blood in Stool"),
    (r"bloody stool", "Blood in Stool"),
    (r"blood in urine", "Blood in Urine"),
    (r"bloody urine", "Blood in Urine"),
    (r"blurred vision", "Blurred Vision"),
    (r"cant see clearly", "Blurred Vision"),
    (r"can't see clearly", "Blurred Vision"),
    (r"cloudy vision", "Blurred Vision"),
    (r"confused", "Confusion"),
    (r"cant think straight", "Confusion"),
    (r"can't think straight", "Confusion"),
    (r"mental fog", "Confusion"),
    (r"loss of consciousness", "Unconsciousness"),
    (r"knocked out", "Unconsciousness"),
    (r"seizure", "Seizure"),
    (r"convulsion", "Seizure"),
    (r"shivering", "Chills"),
    (r"night sweats", "Sweating"),
    (r"excessive sweating", "Sweating"),
    (r"swollen legs", "Swollen Legs"),
    (r"leg swelling", "Swollen Legs"),
    (r"swollen joints", "Swelling Joints"),
    (r"swelling joints", "Swelling Joints"),
    (r"stiff neck", "Stiff Neck"),
    (r"neck stiffness", "Stiff Neck"),
    (r"yellow eyes", "Yellowing of Eyes"),
    (r"yellow skin", "Yellowish Skin"),
    (r"dark urine", "Dark Urine"),
    (r"brown urine", "Dark Urine"),
    (r"tea colored urine", "Dark Urine"),
    (r"fast heart rate", "Fast Heart Rate"),
    (r"rapid heartbeat", "Fast Heart Rate"),
    (r"rapid heart rate", "Fast Heart Rate"),
    (r"weakness in limbs", "Weakness in Limbs"),
    (r"limb weakness", "Weakness in Limbs"),
    (r"loss of balance", "Loss of Balance"),
    (r"loss of smell", "Loss of Smell"),
    (r"cant smell", "Loss of Smell"),
    (r"can't smell", "Loss of Smell"),
    (r"no smell", "Loss of Smell"),
    (r"foul smell of urine", "Foul Smell of Urine"),
    (r"smelly urine", "Foul Smell of Urine"),
    (r"passage of gases", "Passage of Gases"),
    (r"gas", "Passage of Gases"),
    (r"flatulence", "Passage of Gases"),
    (r"lack of concentration", "Lack of Concentration"),
    (r"cant concentrate", "Lack of Concentration"),
    (r"can't concentrate", "Lack of Concentration"),
    (r"pus filled pimples", "Pus Filled Pimples"),
    (r"painful walking", "Painful Walking"),
    (r"hurts to walk", "Painful Walking"),
    (r"prominent veins on calf", "Prominent Veins on Calf"),
    (r"silver like dusting", "Silver Like Dusting"),
    (r"small dents in nails", "Small Dents in Nails"),
    (r"inflammatory nails", "Inflammatory Nails"),
    (r"red sore around nose", "Red Sore Around Nose"),
    (r"yellow crust ooze", "Yellow Crust Ooze"),
    (r"drying and tingling lips", "Drying and Tingling Lips"),
    (r"puffy face and eyes", "Puffy Face and Eyes"),
    (r"enlarged thyroid", "Enlarged Thyroid"),
    (r"goiter", "Enlarged Thyroid"),
    (r"brittle nails", "Brittle Nails"),
    (r"swollen extremeties", "Swollen Extremeties"),
    (r"excessive hunger", "Excessive Hunger"),
    (r"always hungry", "Excessive Hunger"),
    (r"increased appetite", "Increased Appetite"),
    (r"history of alcohol consumption", "History of Alcohol Consumption"),
    (r"receiving blood transfusion", "Receiving Blood Transfusion"),
    (r"receiving unsterile injections", "Receiving Unsterile Injections"),
    (r"family history", "Family History"),
    (r"extra marital contacts", "Extra Marital Contacts"),
    (r"toxic look typhos", "Toxic Look (Typhos)"),
    (r"altered sensorium", "Altered Sensorium"),
    (r"red spot over body", "Red Spots Over Body"),
    (r"red spots over body", "Red Spots Over Body"),
    (r"swelled lymph nodes", "Swelled Lymph Nodes"),
    (r"swollen lymph nodes", "Swelled Lymph Nodes"),
    (r"abnormal menstruation", "Abnormal Menstruation"),
    (r"irregular periods", "Abnormal Menstruation"),
    (r"visual disturbances", "Visual Disturbances"),
    (r"blurred and distorted vision", "Blurred and Distorted Vision"),
    (r"continuous feel of urine", "Continuous Feel of Urine"),
    (r"continuous sneezing", "Continuous Sneezing"),
    (r"sneezing a lot", "Continuous Sneezing"),
    (r"cold hands and feets", "Cold Hands and Feets"),
    (r"cold hands", "Cold Hands and Feets"),
    (r"cold feet", "Cold Hands and Feets"),
    (r"mood swings", "Mood Swings"),
    (r"weight gain", "Weight Gain"),
    (r"gaining weight", "Weight Gain"),
    (r"spinning movements", "Spinning Movements"),
    (r"movement stiffness", "Movement Stiffness"),
    (r"weakness of one body side", "Weakness of One Body Side"),
    (r"bladder discomfort", "Bladder Discomfort"),
    (r"internal itching", "Internal Itching"),
    (r"dischromic patches", "Dischromic Patches"),
    (r"watering from eyes", "Watering from Eyes"),
    (r"tearing eyes", "Watering from Eyes"),
    (r"mucoid sputum", "Mucoid Sputum"),
    (r"rusty sputum", "Rusty Sputum"),
    (r"blood in sputum", "Bloody Phlegm"),
    (r"bloody phlegm", "Bloody Phlegm"),
    (r"stomach bleeding", "Stomach Bleeding"),
    (r"gi bleed", "Stomach Bleeding"),
    (r"distention of abdomen", "Distention of Abdomen"),
    (r"bloated abdomen", "Distention of Abdomen"),
    (r"abdominal distension", "Distention of Abdomen"),
    (r"swelling of stomach", "Swelling of Stomach"),
    (r"fluid overload", "Fluid Overload"),
    (r"acute liver failure", "Acute Liver Failure"),
    (r"coma", "Coma"),
    (r"scurring", "Scurring"),
    (r"skin peeling", "Skin Peeling"),
    (r"blackheads", "Blackheads"),
    (r"blister", "Blister"),
    # Kenyan / local phrasing
    (r"tired all the time", "Fatigue"),
    (r"shivering badly", "Chills"),
    (r"running stomach", "Diarrhea"),
    (r"kuchoka sana", "Fatigue"),
    (r"homakali", "High Fever"),
    (r"homa kali", "High Fever"),
    (r"joto kali", "High Fever"),
    (r"baridi kali", "Chills"),
    (r"kutetemeka", "Chills"),
    (r"tumbo kuumwa", "Abdominal Pain"),
    (r"tumbo inaenda", "Diarrhea"),
    (r"kukojoa uchungu", "Burning Micturition"),
    (r"kukojoa mara nyingi", "Frequent Urination"),
    (r"kunywa maji sana", "Polydipsia"),
    (r"shingo ngumu", "Stiff Neck"),
    (r"sijisikii vizuri", "Malaise"),
    (r"sikupendi kula", "Loss of Appetite"),
    (r"uchovu", "Fatigue"),
    # Expanded Swahili phrases
    (r"kichwa kuumwa", "Headache"),
    (r"kichwa kupiga", "Headache"),
    (r"mgongo kuumwa", "Back Pain"),
    (r"kifua kuumwa", "Chest Pain"),
    (r"kifua kukaza", "Chest Pain"),
    (r"mshipa kuumwa", "Muscle Pain"),
    (r"viungo kuumwa", "Joint Pain"),
    (r"koo kuumwa", "Sore Throat"),
    (r"pua kujaa maji", "Runny Nose"),
    (r"pua kufungika", "Nasal Congestion"),
    (r"jicho kuharibika", "Blurred Vision"),
    (r"mwili kulegea", "Fatigue"),
    (r"mwili kudhoofu", "Fatigue"),
    (r"usingizi kukosa", "Insomnia"),
    (r"moyo kupiga kasi", "Palpitations"),
    (r"moyo kupiga mno", "Palpitations"),
    (r"ngozi kujaa madoa", "Skin Rash"),
    (r"ngozi kutu", "Itching"),
    (r"kutokwa na jasho", "Sweating"),
    (r"jasho kupita kiasi", "Sweating"),
    (r"kupoteza uzito", "Weight Loss"),
    (r"kupata uzito", "Weight Gain"),
    (r"njaa kupita kiasi", "Excessive Hunger"),
    (r"njaa sana", "Excessive Hunger"),
    (r"kukojoa damu", "Blood in Urine"),
    (r"kichefuchefu", "Nausea"),
    (r"kutapika", "Vomiting"),
    (r"tapika", "Vomiting"),
    (r"kikohozi", "Cough"),
    (r"kikohozi kikali", "Persistent Cough"),
    (r"pumzi kukata", "Shortness of Breath"),
    (r"pumzi kushindwa", "Shortness of Breath"),
    (r"debe", "Abdominal Pain"),
    (r"tumbo kubwa", "Distention of Abdomen"),
    (r"tumbo kuchafua", "Diarrhea"),
    (r"tumbo kuhara", "Diarrhea"),
]

# Severity keywords that can be extracted for downstream use
_SEVERITY_KEYWORDS = {
    "mild": "mild", "slight": "mild", "minor": "mild",
    "moderate": "moderate", "persistent": "moderate", "ongoing": "moderate",
    "severe": "severe", "intense": "severe", "extreme": "severe", "unbearable": "severe",
    "worst": "severe", "agonizing": "severe", "excruciating": "severe",
    "sudden": "sudden", "abrupt": "sudden", "rapid onset": "sudden",
    "chronic": "chronic", "long term": "chronic", "recurrent": "chronic",
}

# Common stop words to ignore when tokenizing remaining text
_STOP_WORDS = {
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
    "mustn", "needn", "shan",
    # Severity-only words that should not become symptom chips
    "mild", "moderate", "severe",
    # Swahili stop words
    "na", "ni", "ya", "wa", "kwa", "kama", "pia", "sana", "zaidi",
    "hii", "hizi", "huyu", "wao", "sisi", "mimi", "wewe", "yeye",
    "kwamba", "lakini", "ingawa", "hata", "bila", "baada",
    "kabla", "katika", "juu", "chini", "kati", "mbele", "nyuma",
    "hapa", "pale", "wapi", "nini", "nani", "gani", "vipi",
}


# ============================================================
# SECTION 2 — 15-DISEASE CLINICAL INSIGHTS (TROPICAL FOCUS)
# ============================================================

_CONDITION_INSIGHTS: Dict[str, Dict] = {
    "malaria": {
        "insight": "Malaria is a mosquito-borne disease caused by Plasmodium parasites. Fever with chills and body aches are hallmark symptoms. It is endemic in Kenya and requires prompt diagnosis.",
        "risk_level": "HIGH",
        "suggested_steps": "Immediate blood smear or rapid diagnostic test. Monitor for complications if confirmed. Seek care within 24 hours.",
    },
    "typhoid": {
        "insight": "Typhoid fever is a bacterial infection caused by Salmonella typhi, often presenting with sustained fever and abdominal discomfort. It spreads through contaminated food and water.",
        "risk_level": "HIGH",
        "suggested_steps": "Blood culture and Widal serology. Start empiric antibiotics under medical supervision. Hydration is essential.",
    },
    "dengue": {
        "insight": "Dengue is a viral infection transmitted by Aedes mosquitoes. Watch for warning signs of plasma leakage and bleeding. Platelet monitoring is critical.",
        "risk_level": "HIGH",
        "suggested_steps": "NS1 antigen or IgM serology. Monitor platelet count, hematocrit, and hydration status. Seek care if bleeding develops.",
    },
    "pneumonia": {
        "insight": "Pneumonia is an infection that inflames the air sacs in one or both lungs. It can range from mild to life-threatening, especially in high-risk groups.",
        "risk_level": "HIGH",
        "suggested_steps": "Chest X-ray, CBC, and sputum culture. Empiric antibiotics may be indicated. Monitor oxygen levels.",
    },
    "flu": {
        "insight": "Influenza is a viral respiratory infection that can cause severe complications in high-risk groups. It spreads rapidly during rainy seasons in Kenya.",
        "risk_level": "MEDIUM",
        "suggested_steps": "Rapid influenza test if within 48 hours. Antiviral therapy for high-risk or severe cases. Rest and hydration.",
    },
    "covid-19": {
        "insight": "COVID-19 is caused by SARS-CoV-2. Severity ranges from asymptomatic to severe pneumonia and systemic inflammation. Monitor oxygen saturation.",
        "risk_level": "MEDIUM",
        "suggested_steps": "RT-PCR or rapid antigen test. Monitor oxygen saturation and seek care for respiratory distress. Isolate if positive.",
    },
    "gastroenteritis": {
        "insight": "Gastroenteritis is inflammation of the stomach and intestines, usually infectious in origin. Dehydration is the main risk.",
        "risk_level": "MEDIUM",
        "suggested_steps": "Oral rehydration therapy, stool culture if severe or bloody, and electrolyte monitoring. Seek care for severe dehydration.",
    },
    "food poisoning": {
        "insight": "Food poisoning results from consuming contaminated food or water. Symptoms typically appear within hours and include nausea, vomiting, and diarrhea.",
        "risk_level": "MEDIUM",
        "suggested_steps": "Hydration is critical. Stool culture if severe. Seek care for bloody vomit/stool or severe dehydration.",
    },
    "tuberculosis": {
        "insight": "Tuberculosis is a bacterial infection primarily affecting the lungs. Chronic cough (>2 weeks), weight loss, and night sweats are classic. It is a major public health concern in Kenya.",
        "risk_level": "HIGH",
        "suggested_steps": "Sputum AFB smear and culture, chest X-ray, and GeneXpert MTB/RIF if available. Contact tracing is important.",
    },
    "asthma": {
        "insight": "Asthma is a chronic inflammatory disease of the airways characterized by reversible airflow obstruction. Trigger avoidance and proper inhaler use are essential.",
        "risk_level": "MEDIUM",
        "suggested_steps": "Peak expiratory flow and spirometry. Review inhaler technique and trigger avoidance. Seek emergency care for severe attacks.",
    },
    "uti": {
        "insight": "A urinary tract infection (UTI) can affect the bladder (cystitis) or kidneys (pyelonephritis). Fever with back pain suggests kidney involvement and needs urgent evaluation.",
        "risk_level": "MEDIUM",
        "suggested_steps": "Urinalysis and culture. Start empiric antibiotics; adjust based on culture results. Drink plenty of water.",
    },
    "chickenpox": {
        "insight": "Chickenpox is a highly contagious viral infection causing an itchy, blister-like rash. It is usually self-limiting but can be severe in adults and immunocompromised individuals.",
        "risk_level": "LOW",
        "suggested_steps": "Clinical diagnosis (typical presentation). Rest, hydration, and antihistamines for itching. Avoid scratching.",
    },
    "common cold": {
        "insight": "The common cold is a viral infection of the upper respiratory tract, usually self-limiting. Rest, hydration, and symptomatic relief are usually sufficient.",
        "risk_level": "LOW",
        "suggested_steps": "Supportive care: rest, hydration, and symptomatic relief. Seek care if symptoms worsen or persist >10 days.",
    },
    "meningitis": {
        "insight": "Meningitis is inflammation of the membranes surrounding the brain and spinal cord. It is a medical emergency requiring rapid diagnosis and treatment to prevent brain damage or death.",
        "risk_level": "HIGH",
        "suggested_steps": "Emergency lumbar puncture (CSF analysis), blood culture, and CT brain if indicated. Do not delay treatment.",
    },
    "diabetes warning": {
        "insight": "These symptoms may indicate diabetes mellitus, a chronic metabolic disorder with elevated blood sugar. Early detection and glycemic control prevent complications affecting the eyes, kidneys, nerves, and heart.",
        "risk_level": "MEDIUM",
        "suggested_steps": "Fasting blood glucose, HbA1c, and urine ketones. Endocrinology referral if newly diagnosed. Lifestyle modification is key.",
    },
    # Generic fallbacks for conditions outside the 15-disease focus
    "cardiovascular": {"insight": "Your symptoms may indicate a cardiovascular issue requiring prompt clinical evaluation.", "risk_level": "HIGH", "suggested_steps": "ECG, cardiac enzymes, and cardiology consultation."},
    "respiratory": {"insight": "Your symptoms may indicate a respiratory condition. Pneumonia, asthma exacerbation, or bronchitis should be considered.", "risk_level": "MEDIUM", "suggested_steps": "Chest examination, pulse oximetry, and chest X-ray if indicated."},
    "gastrointestinal": {"insight": "Your symptoms may indicate a gastrointestinal condition such as infection, inflammation, or obstruction.", "risk_level": "MEDIUM", "suggested_steps": "Abdominal examination, stool studies, and imaging if red flags present."},
    "dermatological": {"insight": "Your symptoms suggest a dermatological condition. Allergic, infectious, and autoimmune causes are possible.", "risk_level": "LOW", "suggested_steps": "Dermatological examination and targeted testing based on lesion morphology."},
    "neurological": {"insight": "Your symptoms may indicate a neurological condition. Red-flag symptoms warrant urgent evaluation.", "risk_level": "HIGH", "suggested_steps": "Neurological examination and neuroimaging if red flags are present."},
    "psychiatric": {"insight": "Your reported symptoms may have a psychiatric component. A comprehensive mental health assessment is recommended.", "risk_level": "MEDIUM", "suggested_steps": "Standardized screening tools and psychiatric or psychological evaluation."},
    "endocrine": {"insight": "Your symptoms may suggest an endocrine or metabolic disorder. Glucose and thyroid function should be assessed.", "risk_level": "MEDIUM", "suggested_steps": "Fasting glucose and HbA1c, thyroid function tests. Endocrinology referral if indicated."},
    "heart attack": {"insight": "Acute coronary syndrome is a life-threatening emergency. Chest pain with shortness of breath requires immediate evaluation.", "risk_level": "HIGH", "suggested_steps": "Emergency ECG, troponin levels, and immediate cardiology or emergency department referral."},
    "stroke": {"insight": "Stroke is a time-critical neurological emergency. Rapid assessment and intervention are essential.", "risk_level": "HIGH", "suggested_steps": "Emergency neuroimaging (CT/MRI), neurology referral, and stroke protocol activation."},
    "epilepsy": {"insight": "Epilepsy is a chronic neurological disorder characterized by recurrent seizures. A full neurological workup is needed.", "risk_level": "HIGH", "suggested_steps": "EEG, neuroimaging, and neurology referral for diagnosis and management."},
    "parkinson": {"insight": "Parkinson disease is a progressive neurodegenerative movement disorder. Specialist evaluation is recommended.", "risk_level": "MEDIUM", "suggested_steps": "Neurological examination, dopaminergic imaging, and neurology referral."},
    "peptic ulcer": {"insight": "Peptic ulcer disease involves breaks in the stomach or duodenal lining. Evaluation for H. pylori and NSAID use is important.", "risk_level": "MEDIUM", "suggested_steps": "Upper GI endoscopy, H. pylori testing, and gastroenterology review."},
    "hepatitis": {"insight": "Hepatitis is inflammation of the liver, which may be infectious, toxic, or autoimmune in origin.", "risk_level": "MEDIUM", "suggested_steps": "Liver function tests, viral hepatitis serology, and hepatology referral."},
    "jaundice": {"insight": "Jaundice indicates elevated bilirubin and requires investigation of hepatic, biliary, or hemolytic causes.", "risk_level": "MEDIUM", "suggested_steps": "Liver function tests, abdominal ultrasound, and gastroenterology or hepatology referral."},
    "bronchitis": {"insight": "Bronchitis is inflammation of the bronchial tubes, often following a viral infection.", "risk_level": "MEDIUM", "suggested_steps": "Clinical evaluation, chest examination, and pulmonology review if recurrent."},
    "copd": {"insight": "COPD is a chronic inflammatory lung disease causing airflow limitation. Smoking cessation and inhaler optimization are key.", "risk_level": "MEDIUM", "suggested_steps": "Spirometry, chest X-ray, and pulmonology referral."},
    "hypothyroidism": {"insight": "Hypothyroidism is deficient thyroid hormone production. It can cause fatigue, weight gain, and cold intolerance.", "risk_level": "MEDIUM", "suggested_steps": "TSH and free T4 testing. Endocrinology referral if severe or complicated."},
    "hyperthyroidism": {"insight": "Hyperthyroidism is excess thyroid hormone production. It can cause palpitations, weight loss, and heat intolerance.", "risk_level": "MEDIUM", "suggested_steps": "TSH, free T4, and T3 testing. Endocrinology referral for definitive therapy."},
    "chronic kidney disease": {"insight": "CKD is progressive loss of kidney function over time. Early detection and risk-factor modification are critical.", "risk_level": "HIGH", "suggested_steps": "Serum creatinine, eGFR, urinalysis, and nephrology referral."},
    "psoriasis": {"insight": "Psoriasis is a chronic immune-mediated skin disease. It may be associated with psoriatic arthritis and cardiovascular risk.", "risk_level": "LOW", "suggested_steps": "Dermatological examination and topical or systemic therapy as indicated."},
    "eczema": {"insight": "Eczema (atopic dermatitis) is a chronic inflammatory skin condition. Trigger avoidance and skin barrier repair are central.", "risk_level": "LOW", "suggested_steps": "Dermatological examination, emollient therapy, and topical anti-inflammatories."},
    "acne": {"insight": "Acne is a common pilosebaceous disorder. Severity guides therapy from topical agents to systemic treatment.", "risk_level": "LOW", "suggested_steps": "Dermatological assessment and graded topical or oral therapy."},
    "osteoporosis": {"insight": "Osteoporosis is reduced bone mineral density increasing fracture risk. Bone density testing and fall prevention are key.", "risk_level": "MEDIUM", "suggested_steps": "DEXA scan, calcium and vitamin D assessment, and orthopedic or endocrine referral."},
    "unknown": {"insight": "Based on the reported symptoms, a clear pattern is not recognized. Further clinical evaluation is recommended.", "risk_level": "MEDIUM", "suggested_steps": "Complete physical examination, relevant laboratory tests, and specialist referral as indicated."},
}


def _normalize_token(token: str) -> str:
    token = token.lower().strip().replace("_", " ").replace("-", " ")
    token = re.sub(r"\s+", " ", token)
    return token


def _extract_phrases(text: str) -> List[str]:
    """Extract canonical symptoms from natural-language text using phrase patterns."""
    text_lower = text.lower()
    found = []
    matched_spans = []
    # Sort by phrase length descending so longer matches win
    for pattern, canonical in sorted(_PHRASE_PATTERNS, key=lambda x: len(x[0]), reverse=True):
        for m in re.finditer(pattern, text_lower):
            # Avoid overlapping matches
            overlap = False
            for start, end in matched_spans:
                if not (m.end() <= start or m.start() >= end):
                    overlap = True
                    break
            if not overlap:
                matched_spans.append((m.start(), m.end()))
                found.append(canonical)
    return found


def _extract_severity(text: str) -> Optional[str]:
    """Extract the most severe severity keyword from text."""
    text_lower = text.lower()
    found = []
    for keyword, level in _SEVERITY_KEYWORDS.items():
        if keyword in text_lower:
            found.append(level)
    if not found:
        return None
    # Priority: severe > moderate > mild
    if "severe" in found:
        return "severe"
    if "moderate" in found:
        return "moderate"
    if "mild" in found:
        return "mild"
    if "sudden" in found:
        return "sudden"
    if "chronic" in found:
        return "chronic"
    return found[0]


def normalize_symptoms(symptoms_text: str) -> str:
    """
    Normalize raw symptom text into canonical symptom names.

    Supports:
    - commas, semicolons, newlines
    - natural language and short phrases
    - sentence-style descriptions
    - multi-word symptom understanding
    - typo-resistant alias mapping
    - duplicate removal
    """
    if not symptoms_text:
        return ""

    # Step 1: Extract multi-word phrases first
    phrase_matches = _extract_phrases(symptoms_text)

    cleaned = []
    seen = set()

    # Add phrase matches first
    for canonical in phrase_matches:
        key = canonical.lower()
        if key not in seen and canonical:
            seen.add(key)
            cleaned.append(canonical)

    # Step 2: Build remaining text by removing matched phrase spans
    text_lower = symptoms_text.lower()
    matched_spans = []
    for pattern, canonical in sorted(_PHRASE_PATTERNS, key=lambda x: len(x[0]), reverse=True):
        for m in re.finditer(pattern, text_lower):
            overlap = False
            for start, end in matched_spans:
                if not (m.end() <= start or m.start() >= end):
                    overlap = True
                    break
            if not overlap:
                matched_spans.append((m.start(), m.end()))

    remaining = ""
    last = 0
    for start, end in sorted(matched_spans):
        remaining += text_lower[last:start]
        last = end
    remaining += text_lower[last:]

    # Step 3: Tokenize remaining words and try unigram / bigram matching
    words = re.findall(r"[a-zA-Z_]+", remaining)
    i = 0
    while i < len(words):
        w = words[i].lower()
        if w in _STOP_WORDS or len(w) < 2:
            i += 1
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
        # Try unigram
        if w in _SYMPTOM_ALIASES:
            cn = _SYMPTOM_ALIASES[w]
        else:
            cn = w.capitalize()
        k = cn.lower()
        if k not in seen and cn:
            seen.add(k)
            cleaned.append(cn)
        i += 1

    return ", ".join(cleaned)


def symptoms_to_chips(symptoms_text: str) -> List[str]:
    clean = normalize_symptoms(symptoms_text)
    if not clean:
        return []
    return [s.strip() for s in clean.split(",") if s.strip()]


def extract_severity_from_text(symptoms_text: str) -> Optional[str]:
    """Public helper to extract severity keywords from symptom text."""
    return _extract_severity(symptoms_text)


# ============================================================
# SECTION 3 — IMPROVED AI INSIGHT GENERATION
# ============================================================

def generate_ai_insight(predicted_condition: Optional[str], symptoms: str, priority: str) -> Dict:
    condition = (predicted_condition or "").lower().strip()
    if condition and condition in _CONDITION_INSIGHTS:
        data = _CONDITION_INSIGHTS[condition].copy()
        data["risk_level"] = priority if priority in ("LOW", "MEDIUM", "HIGH") else data["risk_level"]
        return data
    for key, data in _CONDITION_INSIGHTS.items():
        if not condition:
            break
        if key in condition or condition in key:
            result = data.copy()
            result["risk_level"] = priority if priority in ("LOW", "MEDIUM", "HIGH") else result["risk_level"]
            return result
    return {
        "insight": f"Based on the reported symptoms ({symptoms}), further clinical evaluation is recommended.",
        "risk_level": priority if priority in ("LOW", "MEDIUM", "HIGH") else "MEDIUM",
        "suggested_steps": "Complete physical examination, relevant laboratory tests, and specialist referral as indicated.",
    }


def generate_acknowledgement(symptoms: str, condition: Optional[str]) -> str:
    chips = symptoms_to_chips(symptoms)
    condition_text = f"Your presentation is suggestive of {condition}. " if condition else ""
    if chips:
        return f"{condition_text}I have reviewed your clinical presentation. You report the following symptoms: {', '.join(chips)}. Based on your reported history, I have prepared the assessment and recommendations below."
    return f"{condition_text}I have reviewed your clinical presentation and prepared the following assessment and recommendations."



def generate_advice(condition: Optional[str], priority: str) -> str:
    condition_text = condition or "this condition"
    if priority == "HIGH":
        return f"Given the clinical presentation of {condition_text}, this requires close monitoring and prompt medical attention. Please adhere strictly to the recommended investigations and treatment plan. Seek emergency care immediately should you develop any red-flag symptoms including difficulty breathing, chest pain, altered consciousness, or uncontrolled bleeding."
    elif priority == "MEDIUM":
        return f"Your symptoms are consistent with {condition_text} and warrant careful observation. I recommend adequate rest, maintaining good hydration, and following the prescribed management plan. Please arrange a follow-up consultation within 24–48 hours, or sooner if your symptoms worsen or new concerning features develop."
    return f"Your symptoms are consistent with a mild presentation of {condition_text}. I recommend rest, adequate fluid intake, and symptomatic care at home. Should your symptoms persist beyond 3–5 days or interfere with your daily activities, please schedule a routine clinic review."



def generate_suggested_tests(condition: Optional[str]) -> str:
    condition_lower = (condition or "").lower()
    test_map = {
        "malaria": "- Thick and thin blood smear\n- Rapid diagnostic test (RDT)\n- Complete Blood Count (CBC)",
        "typhoid": "- Blood culture\n- Widal test\n- CBC with differential",
        "dengue": "- NS1 antigen test\n- Dengue IgM/IgG serology\n- CBC (platelet count)",
        "tuberculosis": "- Sputum AFB smear and culture\n- Chest X-ray\n- GeneXpert MTB/RIF",
        "pneumonia": "- Chest X-ray\n- CBC\n- Sputum culture\n- Blood culture",
        "asthma": "- Peak expiratory flow\n- Spirometry\n- Chest X-ray (if first episode)",
        "diabetes warning": "- Fasting blood glucose\n- HbA1c\n- Urine ketones\n- Renal function tests",
        "diabetes": "- Fasting blood glucose\n- HbA1c\n- Lipid profile\n- Renal function tests",
        "hypertension": "- Multiple BP readings\n- ECG\n- Renal function tests\n- Lipid profile",
        "heart disease": "- ECG\n- Troponin levels\n- Echocardiogram\n- Stress test",
        "migraine": "- Clinical evaluation\n- CT/MRI brain (if red flags)\n- Vision assessment",
        "gerd": "- Trial of PPI therapy\n- Upper GI endoscopy (if alarm symptoms)",
        "depression": "- PHQ-9 questionnaire\n- Thyroid function tests\n- CBC",
        "anxiety": "- GAD-7 questionnaire\n- Thyroid function tests\n- CBC",
        "common cold": "- Clinical diagnosis\n- Rapid strep test (if sore throat)",
        "flu": "- Rapid influenza test\n- CBC\n- Chest X-ray (if pneumonia suspected)",
        "covid-19": "- RT-PCR or rapid antigen test\n- CBC\n- CRP\n- Chest X-ray",
        "covid": "- RT-PCR or rapid antigen test\n- CBC\n- CRP\n- Chest X-ray",
        "arthritis": "- X-rays of affected joints\n- RF and anti-CCP antibodies\n- ESR and CRP",
        "skin rash": "- Visual examination\n- Skin scraping (if fungal)\n- Patch testing",
        "allergic": "- Clinical assessment\n- Specific IgE testing\n- Skin prick test",
        "gastroenteritis": "- Stool culture (if severe)\n- CBC\n- Electrolyte panel",
        "food poisoning": "- Stool culture\n- Blood culture (if high fever)\n- CBC and electrolytes",
        "urinary tract infection": "- Urinalysis and culture\n- CBC\n- Renal function tests",
        "uti": "- Urinalysis and culture\n- CBC\n- Renal function tests",
        "anemia": "- CBC with differential\n- Ferritin\n- Vitamin B12 and folate",
        "chickenpox": "- Clinical diagnosis (typical presentation)\n- Viral PCR or culture (if atypical)",
        "meningitis": "- Lumbar puncture (CSF analysis)\n- Blood culture\n- CBC and CRP\n- CT brain (if indicated)",
        # Generic category fallbacks
        "cardiovascular": "- ECG\n- Troponin/CK-MB\n- Echocardiogram\n- Lipid profile",
        "respiratory": "- Pulse oximetry\n- Chest X-ray\n- CBC\n- Sputum analysis",
        "gastrointestinal": "- Stool studies\n- Abdominal ultrasound\n- CBC and electrolytes",
        "dermatological": "- Visual skin examination\n- Skin scraping or biopsy if indicated",
        "neurological": "- Neurological examination\n- CT/MRI brain if red flags\n- EEG if seizure suspected",
        "psychiatric": "- PHQ-9 / GAD-7 screening\n- Thyroid function tests\n- Substance use screening",
        "endocrine": "- Fasting glucose and HbA1c\n- Thyroid function tests\n- Electrolytes",
    }
    for key, tests in test_map.items():
        if key in condition_lower:
            return tests
    return "- Complete Blood Count (CBC)\n- Basic metabolic panel\n- Relevant imaging based on clinical findings"


def generate_urgency(priority: str) -> str:
    if priority == "HIGH":
        return "URGENT — This is a high-priority clinical presentation. You should proceed to the nearest emergency department or call emergency services (999/112) immediately if you experience any of the following: difficulty breathing, chest pain, severe or worsening weakness, altered consciousness, confusion, seizures, uncontrolled bleeding, or fainting. Do not delay seeking care."
    elif priority == "MEDIUM":
        return "MODERATE PRIORITY — Please book an appointment at the clinic within the next 24–48 hours for in-person evaluation. Seek urgent care sooner if you notice any red-flag symptoms such as high persistent fever, severe pain, difficulty breathing, or new neurological symptoms (confusion, severe headache, weakness)."
    return "ROUTINE — Your condition appears stable for home management. Monitor your symptoms and maintain a symptom diary. Schedule a routine clinic appointment within the next 5–7 days if symptoms persist, worsen, or begin to affect your daily functioning."

