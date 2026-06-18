"""create backtest run

Revision ID: 20260618_0005
Revises: 20260618_0004
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0005"
down_revision: str | None = "20260618_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "backtest_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_name", sa.String(length=128), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("total_return", sa.Numeric(18, 6), nullable=True),
        sa.Column("annualized_return", sa.Numeric(18, 6), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(18, 6), nullable=True),
        sa.Column("sharpe_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("volatility", sa.Numeric(18, 6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_backtest_run_strategy_config",
        "backtest_run",
        ["strategy_name", "config_version"],
    )
    op.create_index(
        "ix_backtest_run_status_started_at",
        "backtest_run",
        ["status", "started_at"],
    )
    op.create_index(
        "ix_backtest_run_date_range",
        "backtest_run",
        ["start_date", "end_date"],
    )

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


def downgrade() -> None:
    op.drop_index(
        "ix_backtest_equity_point_run_trade_date",
        table_name="backtest_equity_point",
    )
    op.drop_table("backtest_equity_point")
    op.drop_index("ix_backtest_run_date_range", table_name="backtest_run")
    op.drop_index("ix_backtest_run_status_started_at", table_name="backtest_run")
    op.drop_index("ix_backtest_run_strategy_config", table_name="backtest_run")
    op.drop_table("backtest_run")
