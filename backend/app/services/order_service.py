"""
Order creation: book a lab test or order a medicine. Creates an Order row with item_type, item_id, total_amount.
Used by patient routes POST /api/patient/orders/lab-test and .../orders/medicine.
"""
from ..extensions import db
from ..models import Order, LabTest, Medicine


def create_lab_test_order(user_id: int, lab_test_id: int) -> Order:
    """
    Create an order for a lab test. Raises ValueError if lab_test_id not found.
    """
    lab_test = LabTest.query.get(lab_test_id)
    if lab_test is None:
        raise ValueError("Lab test not found")
    order = Order(
        user_id=user_id,
        item_type="lab_test",
        item_id=lab_test_id,
        total_amount=lab_test.price,
        payment_status="pending",
    )
    db.session.add(order)
    db.session.commit()
    db.session.refresh(order)
    return order


def create_medicine_order(user_id: int, medicine_id: int) -> Order:
    """
    Create an order for a medicine. Raises ValueError if medicine not found or out of stock.
    Atomically decrements stock to prevent race-condition overselling.
    """
    medicine = Medicine.query.get(medicine_id)
    if medicine is None:
        raise ValueError("Medicine not found")
    if medicine.stock_level < 1:
        raise ValueError("Medicine out of stock")

    # Atomic stock decrement using UPDATE to prevent race conditions
    from sqlalchemy import update
    result = db.session.execute(
        update(Medicine)
        .where(Medicine.id == medicine_id, Medicine.stock_level > 0)
        .values(stock_level=Medicine.stock_level - 1)
    )
    if result.rowcount == 0:
        raise ValueError("Medicine out of stock")

    order = Order(
        user_id=user_id,
        item_type="medicine",
        item_id=medicine_id,
        total_amount=medicine.price,
        payment_status="pending",
    )
    db.session.add(order)
    db.session.commit()
    db.session.refresh(order)
    return order
