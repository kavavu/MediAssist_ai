"""
Test script for the Hybrid Clinical Prediction Engine.

Run with:
    cd backend && python test_clinical_engine.py
"""

import sys
import os
import importlib.util

# Load the engine module directly to avoid the backend import issue
spec = importlib.util.spec_from_file_location('engine', os.path.join(os.path.dirname(__file__), 'app', 'ml', 'clinical', 'engine.py'))
engine = importlib.util.module_from_spec(spec)
sys.modules['app'] = type(sys)('app')
sys.modules['app.ml'] = type(sys)('app.ml')
sys.modules['app.ml.clinical'] = type(sys)('app.ml.clinical')
sys.modules['app.ml.clinical.engine'] = engine
spec.loader.exec_module(engine)

predict_topk = engine.predict_topk
normalize_symptoms = engine.normalize_symptoms


def print_result(label: str, result: dict):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"{'='*60}")
    if result.get("error"):
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Primary: {result['predicted_condition']} ({result['confidence_score']:.2%})")
        print(f"  Severity: {result['severity']}")
        print(f"  Red Flag: {result['red_flag']}")
        print(f"  Match Quality: {result['match_quality']}")
        print(f"  Cleaned Symptoms: {result['cleaned_symptoms']}")
        print(f"  Top 3:")
        for p in result["top_3_predictions"]:
            print(f"    - {p['condition']}: {p['confidence']:.2%}")
        if result.get("detected_red_flags"):
            print(f"  Detected Red Flags: {result['detected_red_flags']}")
    print()


def test_malaria_classic():
    result = predict_topk("fever, chills, headache, vomiting, sweating")
    print_result("Malaria - Classic Presentation", result)
    assert result["error"] is None, f"Unexpected error: {result['error']}"
    assert result["predicted_condition"] == "Malaria", f"Expected Malaria, got {result['predicted_condition']}"
    assert result["confidence_score"] >= 0.70, f"Confidence too low: {result['confidence_score']}"
    assert result["severity"] == "HIGH"
    print("  PASS\n")


def test_malaria_kenyan_phrasing():
    result = predict_topk("homakali, kutetemeka, kichwa inauma, kunywa maji sana")
    print_result("Malaria - Kenyan Phrasing", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Malaria", f"Expected Malaria, got {result['predicted_condition']}"
    assert result["confidence_score"] >= 0.40
    print("  PASS\n")


def test_typhoid():
    result = predict_topk("fever, abdominal pain, headache, loss of appetite, weakness, constipation")
    print_result("Typhoid - Classic Presentation", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Typhoid", f"Expected Typhoid, got {result['predicted_condition']}"
    assert result["confidence_score"] >= 0.60
    print("  PASS\n")


def test_dengue():
    result = predict_topk("high fever, severe headache, pain behind eyes, muscle pain, rash")
    print_result("Dengue - Classic Presentation", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Dengue", f"Expected Dengue, got {result['predicted_condition']}"
    assert result["confidence_score"] >= 0.60
    print("  PASS\n")


def test_meningitis_red_flag():
    result = predict_topk("fever, stiff neck, severe headache, confusion, vomiting")
    print_result("Meningitis - With Red Flags", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Meningitis", f"Expected Meningitis, got {result['predicted_condition']}"
    assert result["red_flag"] is True
    assert result["severity"] == "HIGH"
    assert len(result["detected_red_flags"]) > 0
    print("  PASS\n")


def test_common_cold():
    result = predict_topk("runny nose, sneezing, sore throat, mild cough")
    print_result("Common Cold", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Common Cold", f"Expected Common Cold, got {result['predicted_condition']}"
    assert result["severity"] == "LOW"
    print("  PASS\n")


def test_invalid_nonsense():
    result = predict_topk("xyzqwerty blorp snizzle fizzbuzz")
    print_result("Invalid - Nonsense Input", result)
    assert result["error"] is not None
    assert "Unable to confidently determine" in result["error"] or "No valid symptoms" in result["error"]
    print("  PASS\n")


def test_invalid_too_short():
    result = predict_topk("a")
    print_result("Invalid - Too Short", result)
    assert result["error"] is not None
    print("  PASS\n")


def test_normalization_misspellings():
    symptoms, cleaned = normalize_symptoms("vomitting, stomache, feever, diarhea")
    print(f"\nTEST: Normalization - Misspellings")
    print(f"  Input:  'vomitting, stomache, feever, diarhea'")
    print(f"  Output: {symptoms}")
    assert "vomiting" in symptoms
    assert "fever" in symptoms
    assert "diarrhea" in symptoms
    print("  PASS\n")


def test_normalization_slang():
    symptoms, cleaned = normalize_symptoms("throwing up, tired all the time, chest feels tight")
    print(f"\nTEST: Normalization - Slang")
    print(f"  Input:  'throwing up, tired all the time, chest feels tight'")
    print(f"  Output: {symptoms}")
    assert "vomiting" in symptoms
    assert "fatigue" in symptoms
    assert "chest tightness" in symptoms
    print("  PASS\n")


def test_confidence_realism():
    result = predict_topk("I feel a bit tired")
    print_result("Confidence Realism - Vague Symptom", result)
    assert result["error"] is not None or result["confidence_score"] < 0.50
    if result["error"] is None:
        assert result["confidence_score"] < 0.60, f"Confidence too high for vague symptom: {result['confidence_score']}"
    print("  PASS\n")


def test_top3_separation():
    result = predict_topk("fever, chills, headache, vomiting, sweating, fatigue")
    print_result("Top-3 Separation - Malaria Symptoms", result)
    preds = result["top_3_predictions"]
    assert len(preds) >= 2
    if len(preds) >= 2:
        gap = preds[0]["confidence"] - preds[1]["confidence"]
        assert gap >= 0.04, f"Top-2 gap too small: {gap}"
    if len(preds) >= 3:
        gap = preds[1]["confidence"] - preds[2]["confidence"]
        assert gap >= 0.02, f"Top-3 gap too small: {gap}"
    print("  PASS\n")


def test_diabetes_warning():
    result = predict_topk("excessive thirst, frequent urination, fatigue, weight loss, blurred vision")
    print_result("Diabetes Warning", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Diabetes Warning", f"Expected Diabetes Warning, got {result['predicted_condition']}"
    print("  PASS\n")


def test_asthma():
    result = predict_topk("wheezing, shortness of breath, cough, chest tightness")
    print_result("Asthma", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Asthma", f"Expected Asthma, got {result['predicted_condition']}"
    print("  PASS\n")


def test_pneumonia():
    result = predict_topk("cough, fever, shortness of breath, chest pain, fatigue")
    print_result("Pneumonia", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Pneumonia", f"Expected Pneumonia, got {result['predicted_condition']}"
    assert result["confidence_score"] >= 0.50
    print("  PASS\n")


def test_uti():
    result = predict_topk("burning urination, frequent urination, pelvic pain")
    print_result("UTI", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "UTI", f"Expected UTI, got {result['predicted_condition']}"
    print("  PASS\n")


def test_tuberculosis():
    result = predict_topk("persistent cough, weight loss, night sweats, fever, fatigue")
    print_result("Tuberculosis", result)
    assert result["error"] is None
    assert result["predicted_condition"] == "Tuberculosis", f"Expected Tuberculosis, got {result['predicted_condition']}"
    assert result["confidence_score"] >= 0.50
    print("  PASS\n")


def run_all_tests():
    print("=" * 60)
    print("MEDIASSIST AI - CLINICAL PREDICTION ENGINE TESTS")
    print("=" * 60)

    tests = [
        test_malaria_classic,
        test_malaria_kenyan_phrasing,
        test_typhoid,
        test_dengue,
        test_meningitis_red_flag,
        test_common_cold,
        test_invalid_nonsense,
        test_invalid_too_short,
        test_normalization_misspellings,
        test_normalization_slang,
        test_confidence_realism,
        test_top3_separation,
        test_diabetes_warning,
        test_asthma,
        test_pneumonia,
        test_uti,
        test_tuberculosis,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
