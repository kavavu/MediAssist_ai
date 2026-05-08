"""
Seed sample lab tests and medicines when the catalog is empty.
Called on app startup from app/__init__.py. Safe to run multiple times (skips if data exists).
"""
from ..extensions import db
from ..models import LabTest, Medicine, User
from ..services.auth_service import hash_password


def seed_catalog():
    """
    Insert placeholder lab tests, medicines, and sample doctors if none exist.
    Call within an application context.
    """
    if LabTest.query.count() > 0 and Medicine.query.count() > 0:
        return
    if LabTest.query.count() == 0:
        _seed_lab_tests()
    if Medicine.query.count() == 0:
        _seed_medicines()
    _seed_doctors()
    db.session.commit()


def _seed_lab_tests():
    """Insert default lab tests. Prices in Kenyan Shillings (KSh)."""
    items = [
        ("Complete Blood Count (CBC)", "Measures blood cells and hemoglobin", 1200.00),
        ("Blood Glucose Fasting", "Fasting blood sugar level", 500.00),
        ("Lipid Profile", "Cholesterol and triglycerides", 1800.00),
        ("Thyroid Function (TSH)", "Thyroid stimulating hormone", 1500.00),
        ("Liver Function Test", "ALT, AST, bilirubin", 1200.00),
        ("Kidney Function Test", "Creatinine, urea", 1200.00),
        ("Urine Analysis", "Routine urine test", 400.00),
    ]
    for name, description, price in items:
        db.session.add(LabTest(name=name, description=description, price=price))


def _seed_medicines():
    """Insert default medicines. Prices in Kenyan Shillings (KSh)."""
    items = [
        ("Paracetamol 500mg", "Cosmos Ltd", 35.00, 500, False),
        ("Ibuprofen 400mg", "Dawa Ltd", 50.00, 300, False),
        ("Amoxicillin 250mg", "Universal Corp", 120.00, 200, True),
        ("Omeprazole 20mg", "Cosmos Ltd", 80.00, 250, False),
        ("Cetirizine 10mg", "Dawa Ltd", 60.00, 400, False),
        ("Metformin 500mg", "Universal Corp", 150.00, 150, True),
    ]
    for name, manufacturer, price, stock, requires_prescription in items:
        db.session.add(Medicine(
            name=name,
            manufacturer=manufacturer,
            price=price,
            stock_level=stock,
            requires_prescription=requires_prescription,
        ))


def _seed_doctors():
    """Insert sample doctors with specializations if none exist."""
    if User.query.filter_by(role="doctor").count() > 0:
        return
    doctors = [
        ("Dr. Sarah Kimani", "sarah@mediassist.local", "General Doctor"),
        ("Dr. James Ochieng", "james@mediassist.local", "Endocrinologist"),
        ("Dr. Amina Hassan", "amina@mediassist.local", "Pulmonologist"),
        ("Dr. Peter Mwangi", "peter@mediassist.local", "Cardiologist"),
        ("Dr. Grace Wanjiku", "grace@mediassist.local", "Neurologist"),
        ("Dr. David Otieno", "david@mediassist.local", "Dermatologist"),
    ]
    for name, email, specialization in doctors:
        db.session.add(User(
            name=name,
            email=email,
            password_hash=hash_password("doctor123"),
            role="doctor",
            specialization=specialization,
            is_available=True,
            current_load=0,
            is_verified=True,
        ))
