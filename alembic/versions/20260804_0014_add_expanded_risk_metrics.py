"""Add expanded active and downside risk metrics.

Revision ID: 20260804_0014
Revises: 20260803_0013
Create Date: 2026-08-04
"""

import sqlalchemy as sa

from alembic import op

revision = "20260804_0014"
down_revision = "20260803_0013"
branch_labels = None
depends_on = None


def _strategy_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("sortino_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("calmar_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("longest_drawdown_duration_sessions", sa.Integer(), nullable=True),
        sa.Column("longest_drawdown_peak_date", sa.Date(), nullable=True),
        sa.Column("longest_drawdown_trough_date", sa.Date(), nullable=True),
        sa.Column("longest_drawdown_recovery_date", sa.Date(), nullable=True),
    ]


def _benchmark_columns() -> list[sa.Column[object]]:
    return [
        *_strategy_columns(),
        sa.Column("tracking_error", sa.Numeric(18, 6), nullable=True),
        sa.Column("information_ratio", sa.Numeric(18, 6), nullable=True),
    ]


def upgrade() -> None:
    for column in _strategy_columns():
        op.add_column("backtest_run", column)
    for column in _benchmark_columns():
        op.add_column("backtest_benchmark", column)


def downgrade() -> None:
    for column in reversed(_benchmark_columns()):
        op.drop_column("backtest_benchmark", column.name)
    for column in reversed(_strategy_columns()):
        op.drop_column("backtest_run", column.name)
