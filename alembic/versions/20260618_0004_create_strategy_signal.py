"""create strategy signal

Revision ID: 20260618_0004
Revises: 20260618_0003
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0004"
down_revision: str | None = "20260618_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategy_signal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("signal_date", sa.Date(), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        "ix_strategy_signal_date_config",
        "strategy_signal",
        ["signal_date", "config_version"],
    )
    op.create_index(
        "ix_strategy_signal_status_generated_at",
        "strategy_signal",
        ["status", "generated_at"],
    )

    op.create_table(
        "strategy_signal_position",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_signal_id", sa.Integer(), nullable=False),
        sa.Column("etf_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Numeric(18, 6), nullable=True),
        sa.Column("target_weight", sa.Numeric(10, 6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["etf_id"], ["etf_info.id"]),
        sa.ForeignKeyConstraint(["strategy_signal_id"], ["strategy_signal.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "strategy_signal_id",
            "etf_id",
            name="uq_strategy_signal_position_signal_etf",
        ),
    )
    op.create_index(
        "ix_strategy_signal_position_signal",
        "strategy_signal_position",
        ["strategy_signal_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_strategy_signal_position_signal", table_name="strategy_signal_position")
    op.drop_table("strategy_signal_position")
    op.drop_index("ix_strategy_signal_status_generated_at", table_name="strategy_signal")
    op.drop_index("ix_strategy_signal_date_config", table_name="strategy_signal")
    op.drop_table("strategy_signal")
