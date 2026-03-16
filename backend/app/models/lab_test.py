"""
Lab test catalog: available tests and pricing.
"""
from ..extensions import db


class LabTest(db.Model):
    """
    A lab test offered by the system (name, description, price).
    """

    __tablename__ = "lab_tests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    def __repr__(self):
        return f"<LabTest {self.name}>"
