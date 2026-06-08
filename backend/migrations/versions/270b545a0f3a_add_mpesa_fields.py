"""add_mpesa_fields

Revision ID: 270b545a0f3a
Revises: 
Create Date: 2026-05-27 22:08:11.887711

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '270b545a0f3a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Only add the new payment columns — leave existing tables untouched
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('displayed_amount', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('merchant_request_id', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column('mpesa_receipt_number', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('failure_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('paid_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('paid_at')
        batch_op.drop_column('failure_reason')
        batch_op.drop_column('mpesa_receipt_number')
        batch_op.drop_column('phone_number')
        batch_op.drop_column('merchant_request_id')
        batch_op.drop_column('displayed_amount')
