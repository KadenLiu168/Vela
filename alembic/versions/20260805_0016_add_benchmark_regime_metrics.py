"""Add benchmark regime performance metrics.

Revision ID: 20260805_0016
Revises: 20260804_0015
Create Date: 2026-08-05
"""

import sqlalchemy as sa

from alembic import op

revision = "20260805_0016"
down_revision = "20260804_0015"
branch_labels = None
depends_on = None

_COLUMNS = [
    sa.Column("capm_alpha", sa.Numeric(18, 6), nullable=True),
    sa.Column("capm_beta", sa.Numeric(18, 6), nullable=True),
    sa.Column("capm_r_squared", sa.Numeric(18, 6), nullable=True),
    sa.Column("capm_observation_count", sa.Integer(), nullable=True),
    sa.Column("up_capture_ratio", sa.Numeric(18, 6), nullable=True),
    sa.Column("up_capture_observation_count", sa.Integer(), nullable=True),
    sa.Column("down_capture_ratio", sa.Numeric(18, 6), nullable=True),
    sa.Column("down_capture_observation_count", sa.Integer(), nullable=True),
]


def upgrade() -> None:
    for column in _COLUMNS:
        op.add_column("backtest_benchmark", column)


def downgrade() -> None:
    for column in reversed(_COLUMNS):
        op.drop_column("backtest_benchmark", column.name)
