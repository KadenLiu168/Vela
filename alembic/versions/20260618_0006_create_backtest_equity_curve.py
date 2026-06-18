"""create backtest equity curve

Revision ID: 20260618_0006
Revises: 20260618_0005
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0006"
down_revision: str | None = "20260618_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "backtest_equity_curve",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("net_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("cash", sa.Numeric(18, 6), nullable=False),
        sa.Column("market_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("total_assets", sa.Numeric(18, 6), nullable=False),
        sa.Column("positions_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "backtest_run_id",
            "trade_date",
            name="uq_backtest_equity_curve_run_trade_date",
        ),
    )
    op.create_index(
        "ix_backtest_equity_curve_run_trade_date",
        "backtest_equity_curve",
        ["backtest_run_id", "trade_date"],
    )

    op.drop_index(
        "ix_backtest_equity_point_run_trade_date",
        table_name="backtest_equity_point",
    )
    op.drop_table("backtest_equity_point")


def downgrade() -> None:
    op.create_table(
        "backtest_equity_point",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("net_value", sa.Numeric(18, 6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "backtest_run_id",
            "trade_date",
            name="uq_backtest_equity_point_run_trade_date",
        ),
    )
    op.create_index(
        "ix_backtest_equity_point_run_trade_date",
        "backtest_equity_point",
        ["backtest_run_id", "trade_date"],
    )

    op.drop_index(
        "ix_backtest_equity_curve_run_trade_date",
        table_name="backtest_equity_curve",
    )
    op.drop_table("backtest_equity_curve")
