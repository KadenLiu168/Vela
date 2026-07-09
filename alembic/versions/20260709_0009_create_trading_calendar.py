"""create trading_calendar table

Revision ID: 20260709_0009
Revises: 20260709_0008
Create Date: 2026-07-09

This revision creates the ``trading_calendar`` table, which stores the
A-share trading-day calendar synced from akshare ``tool_trade_date_hist_sina``.
It is the authoritative reference for "which days are trading days" used by
data-quality gap detection. ``trade_date`` is the primary key (one row per
trading day); ``source`` records the data origin.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260709_0009"
down_revision: str | None = "20260709_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trading_calendar",
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("trade_date"),
    )


def downgrade() -> None:
    op.drop_table("trading_calendar")
