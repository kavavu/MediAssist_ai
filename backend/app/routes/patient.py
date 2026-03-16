"""
Patient dashboard API (all routes require JWT + role "patient"):

- GET  /api/patient/predictions     → list current user's symptom reports
- GET  /api/patient/lab-tests      → list all lab tests
- GET  /api/patient/medicines       → list all medicines
- POST /api/patient/orders/lab-test → body { lab_test_id } → create order
- POST /api/patient/orders/medicine → body { medicine_id } → create order
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user

from ..models import SymptomReport, LabTest, Medicine, Order
from ..services.order_service import create_lab_test_order, create_medicine_order
from ..utils.decorators import role_required

patient_bp = Blueprint("patient", __name__)


def _symptom_report_payload(r):
    """Serialize a SymptomReport for JSON."""
    return {
        "id": r.id,
        "symptoms_text": r.symptoms_text,
        "predicted_condition": r.predicted_condition,
        "confidence_score": float(r.confidence_score) if r.confidence_score is not None else None,
        "top_predictions": r.top_predictions or None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _lab_test_payload(t):
    """Serialize a LabTest for JSON."""
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "price": float(t.price) if t.price is not None else 0,
    }


def _medicine_payload(m):
    """Serialize a Medicine for JSON."""
    return {
        "id": m.id,
        "name": m.name,
        "manufacturer": m.manufacturer,
        "price": float(m.price) if m.price is not None else 0,
        "stock_level": m.stock_level,
        "requires_prescription": m.requires_prescription,
    }


def _order_payload(o):
    """Serialize an Order for JSON."""
    return {
        "id": o.id,
        "item_type": o.item_type,
        "item_id": o.item_id,
        "total_amount": float(o.total_amount) if o.total_amount is not None else 0,
        "payment_status": o.payment_status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


@patient_bp.get("/predictions")
@jwt_required()
@role_required("patient")
def list_predictions():
    """Return the current user's symptom prediction history (newest first)."""
    user = get_current_user()
    reports = SymptomReport.query.filter_by(user_id=user.id).order_by(SymptomReport.created_at.desc()).all()
    return jsonify({"predictions": [_symptom_report_payload(r) for r in reports]})


@patient_bp.get("/lab-tests")
@jwt_required()
@role_required("patient")
def list_lab_tests():
    """Return all available lab tests."""
    tests = LabTest.query.order_by(LabTest.name).all()
    return jsonify({"lab_tests": [_lab_test_payload(t) for t in tests]})


@patient_bp.get("/medicines")
@jwt_required()
@role_required("patient")
def list_medicines():
    """Return all available medicines."""
    medicines = Medicine.query.order_by(Medicine.name).all()
    return jsonify({"medicines": [_medicine_payload(m) for m in medicines]})


@patient_bp.post("/orders/lab-test")
@jwt_required()
@role_required("patient")
def book_lab_test():
    """Book a lab test. Expects JSON: lab_test_id."""
    data = request.get_json(silent=True) or {}
    lab_test_id = data.get("lab_test_id")
    if lab_test_id is None:
        return jsonify({"message": "Missing lab_test_id"}), 400
    try:
        lab_test_id = int(lab_test_id)
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid lab_test_id"}), 400
    user = get_current_user()
    try:
        order = create_lab_test_order(user_id=user.id, lab_test_id=lab_test_id)
        return jsonify({"message": "Lab test booked", "order": _order_payload(order)}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 404


@patient_bp.post("/orders/medicine")
@jwt_required()
@role_required("patient")
def order_medicine():
    """Order a medicine. Expects JSON: medicine_id."""
    data = request.get_json(silent=True) or {}
    medicine_id = data.get("medicine_id")
    if medicine_id is None:
        return jsonify({"message": "Missing medicine_id"}), 400
    try:
        medicine_id = int(medicine_id)
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid medicine_id"}), 400
    user = get_current_user()
    try:
        order = create_medicine_order(user_id=user.id, medicine_id=medicine_id)
        return jsonify({"message": "Medicine ordered", "order": _order_payload(order)}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
