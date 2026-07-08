"""add strategy signal strategy_id and rename backtest strategy_name

Revision ID: 20260708_0007
Revises: 20260618_0006
Create Date: 2026-07-08

This revision:

1. Adds a non-null ``strategy_id`` column to ``strategy_signal``, backfilling
   every existing row with the project's current strategy id from the YAML
   config. SQLite 3.31+ supports ``ALTER TABLE ADD COLUMN ... NOT NULL
   DEFAULT`` in a single statement.

2. Renames ``backtest_run.strategy_name`` to ``strategy_id`` via SQLite's
   native ``ALTER TABLE ... RENAME COLUMN`` (3.25+) and normalizes every
   row's value to the current strategy id (collapsing legacy casing such as
   ``dual_momentum`` -> ``Dual_momentum``). The existing index follows the
   renamed column automatically.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260708_0007"
down_revision: str | None = "20260618_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CURRENT_STRATEGY_ID = "Dual_momentum"


def upgrade() -> None:
    op.add_column(
        "strategy_signal",
        sa.Column(
            "strategy_id",
            sa.String(length=128),
            nullable=False,
            server_default=_CURRENT_STRATEGY_ID,
        ),
    )

    op.execute(
        sa.text(
            "UPDATE strategy_signal SET strategy_id = :strategy_id "
            "WHERE strategy_id IS NULL OR strategy_id = '' OR strategy_id != :strategy_id"
        ).bindparams(strategy_id=_CURRENT_STRATEGY_ID)
    )

    op.create_index(
        "ix_strategy_signal_strategy_config",
        "strategy_signal",
        ["strategy_id", "config_version"],
    )

    op.drop_index("ix_backtest_run_strategy_config", table_name="backtest_run")

    op.execute(sa.text("ALTER TABLE backtest_run RENAME COLUMN strategy_name TO strategy_id"))

    op.create_index(
        "ix_backtest_run_strategy_config",
        "backtest_run",
        ["strategy_id", "config_version"],
    )

    op.execute(
        sa.text(
            "UPDATE backtest_run SET strategy_id = :strategy_id WHERE strategy_id != :strategy_id"
        ).bindparams(strategy_id=_CURRENT_STRATEGY_ID)
    )


def downgrade() -> None:
    op.drop_index("ix_backtest_run_strategy_config", table_name="backtest_run")
    op.execute(sa.text("ALTER TABLE backtest_run RENAME COLUMN strategy_id TO strategy_name"))
    op.create_index(
        "ix_backtest_run_strategy_config",
        "backtest_run",
        ["strategy_name", "config_version"],
    )

    op.drop_index("ix_strategy_signal_strategy_config", table_name="strategy_signal")
    op.drop_column("strategy_id", table_name="strategy_signal")