"""Add tail-distribution risk metrics.

Revision ID: 20260806_0017
Revises: 20260805_0016
Create Date: 2026-08-06
"""

import sqlalchemy as sa

from alembic import op

revision = "20260806_0017"
down_revision = "20260805_0016"
branch_labels = None
depends_on = None

_COLUMNS = [
    sa.Column("historical_var_95", sa.Numeric(18, 6), nullable=True),
    sa.Column("historical_cvar_95", sa.Numeric(18, 6), nullable=True),
    sa.Column("return_skewness", sa.Numeric(18, 6), nullable=True),
    sa.Column("return_excess_kurtosis", sa.Numeric(18, 6), nullable=True),
    sa.Column("distribution_observation_count", sa.Integer(), nullable=True),
    sa.Column("tail_observation_count", sa.Integer(), nullable=True),
]

_TABLES = ("backtest_run", "backtest_benchmark")


def upgrade() -> None:
    for table in _TABLES:
        for column in _COLUMNS:
            op.add_column(table, column)


def downgrade() -> None:
    for table in reversed(_TABLES):
        for column in reversed(_COLUMNS):
            op.drop_column(table, column.name)
