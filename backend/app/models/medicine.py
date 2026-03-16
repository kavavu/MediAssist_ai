"""
Medicine catalog: available medicines and stock.
"""
from ..extensions import db


class Medicine(db.Model):
    """
    A medicine offered by the system (name, manufacturer, price, stock, prescription requirement).
    """

    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    manufacturer = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock_level = db.Column(db.Integer, nullable=False, default=0)
    requires_prescription = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Medicine {self.name}>"
