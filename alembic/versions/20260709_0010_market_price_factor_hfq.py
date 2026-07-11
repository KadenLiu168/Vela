"""replace adjusted_close with factor_hfq on market_price

Revision ID: 20260709_0010
Revises: 20260709_0009
Create Date: 2026-07-09

This revision drops the legacy ``adjusted_close`` column and adds the
``factor_hfq`` backward-adjustment factor column on ``market_price``.

``adjusted_close`` was always NULL in practice: every provider fetched
unadjusted data and ``base_market_data_provider`` hardcoded it to ``None``,
so ``strategy_price`` always fell back to the unadjusted ``close_price``
(distorting momentum/trend/net-value signals on any ETF with a dividend or
split). The fix stores two raw facts -- the unadjusted ``close_price`` and
the append-only backward-adjustment factor ``factor_hfq`` -- and derives
``strategy_price = close_price * factor_hfq`` (backward-adjusted) at read
time.

``factor_hfq`` is ``Numeric(18, 12) NOT NULL``. The column is added with a
``server_default`` of ``1`` so existing rows survive the NOT NULL constraint
on populated databases; the deployment plan (see the change design) resets
and fully refetches ``market_price`` immediately after, replacing the
placeholder ``1`` with real factors. The default is retained in the schema
harmlessly: new rows always supply the factor via the ORM.

SQLite cannot ``DROP COLUMN`` / ``ADD COLUMN NOT NULL`` without default on
older versions, so ``batch_alter_table`` rebuilds the table to apply both
changes portably.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260709_0010"
down_revision: str | None = "20260709_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("market_price", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "factor_hfq",
                sa.Numeric(precision=18, scale=12),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.drop_column("adjusted_close")


def downgrade() -> None:
    with op.batch_alter_table("market_price", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("adjusted_close", sa.Numeric(precision=18, scale=6), nullable=True)
        )
        batch_op.drop_column("factor_hfq")
