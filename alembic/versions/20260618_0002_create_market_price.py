"""create market price

Revision ID: 20260618_0002
Revises: 20260618_0001
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0002"
down_revision: str | None = "20260618_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_price",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("etf_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("high_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("low_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("adjusted_close", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
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
        sa.ForeignKeyConstraint(["etf_id"], ["etf_info.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("etf_id", "trade_date", name="uq_market_price_etf_trade_date"),
    )
    op.create_index(
        "ix_market_price_etf_trade_date",
        "market_price",
        ["etf_id", "trade_date"],
    )
    op.create_index("ix_market_price_trade_date", "market_price", ["trade_date"])


def downgrade() -> None:
    op.drop_index("ix_market_price_trade_date", table_name="market_price")
    op.drop_index("ix_market_price_etf_trade_date", table_name="market_price")
    op.drop_table("market_price")
