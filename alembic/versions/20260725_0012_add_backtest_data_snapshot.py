"""Add backtest data snapshot.

Revision ID: 20260725_0012
Revises: 20260719_0011
Create Date: 2026-07-25
"""

import sqlalchemy as sa

from alembic import op

revision = "20260725_0012"
down_revision = "20260719_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("backtest_run", sa.Column("data_snapshot_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("backtest_run") as batch_op:
        batch_op.drop_column("data_snapshot_json")
