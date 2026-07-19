"""Add strategy signal provenance.

Revision ID: 20260719_0011
Revises: 20260709_0010
Create Date: 2026-07-19
"""

import sqlalchemy as sa

from alembic import op

revision = "20260719_0011"
down_revision = "20260709_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("strategy_signal", sa.Column("source", sa.String(length=16), nullable=True))
    op.execute("UPDATE strategy_signal SET source = 'legacy'")

    with op.batch_alter_table("strategy_signal", recreate="always") as batch_op:
        batch_op.alter_column("source", existing_type=sa.String(length=16), nullable=False)
        batch_op.add_column(sa.Column("backtest_run_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_strategy_signal_backtest_run_id_backtest_run",
            "backtest_run",
            ["backtest_run_id"],
            ["id"],
        )
        batch_op.create_check_constraint(
            "ck_strategy_signal_source",
            "source IN ('manual', 'scheduled', 'backtest', 'legacy')",
        )
        batch_op.create_check_constraint(
            "ck_strategy_signal_backtest_link",
            "source = 'backtest' OR backtest_run_id IS NULL",
        )

    op.create_index(
        "ix_strategy_signal_backtest_run_id",
        "strategy_signal",
        ["backtest_run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_strategy_signal_backtest_run_id", table_name="strategy_signal")

    with op.batch_alter_table("strategy_signal", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_strategy_signal_backtest_link", type_="check")
        batch_op.drop_constraint("ck_strategy_signal_source", type_="check")
        batch_op.drop_constraint(
            "fk_strategy_signal_backtest_run_id_backtest_run", type_="foreignkey"
        )
        batch_op.drop_column("backtest_run_id")
        batch_op.drop_column("source")
