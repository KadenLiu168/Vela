"""Add persisted backtest benchmarks.

Revision ID: 20260803_0013
Revises: 20260725_0012
Create Date: 2026-08-03
"""

import sqlalchemy as sa

from alembic import op

revision = "20260803_0013"
down_revision = "20260725_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backtest_benchmark",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column("benchmark_key", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("total_return", sa.Numeric(18, 6)),
        sa.Column("annualized_return", sa.Numeric(18, 6)),
        sa.Column("max_drawdown", sa.Numeric(18, 6)),
        sa.Column("sharpe_ratio", sa.Numeric(18, 6)),
        sa.Column("volatility", sa.Numeric(18, 6)),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "backtest_run_id", "benchmark_key", name="uq_backtest_benchmark_run_key"
        ),
    )
    op.create_table(
        "backtest_benchmark_equity_curve",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("benchmark_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("net_value", sa.Numeric(18, 6), nullable=False),
        sa.ForeignKeyConstraint(["benchmark_id"], ["backtest_benchmark.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("benchmark_id", "trade_date", name="uq_backtest_benchmark_curve_date"),
    )


def downgrade() -> None:
    op.drop_table("backtest_benchmark_equity_curve")
    op.drop_table("backtest_benchmark")
