"""create etf info

Revision ID: 20260618_0001
Revises:
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "etf_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("inception_date", sa.Date(), nullable=True),
        sa.Column("expense_ratio", sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
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
        sa.UniqueConstraint("exchange", "symbol", name="uq_etf_info_exchange_symbol"),
    )
    op.create_index("ix_etf_info_exchange", "etf_info", ["exchange"])
    op.create_index("ix_etf_info_is_active", "etf_info", ["is_active"])
    op.create_index("ix_etf_info_symbol", "etf_info", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_etf_info_symbol", table_name="etf_info")
    op.drop_index("ix_etf_info_is_active", table_name="etf_info")
    op.drop_index("ix_etf_info_exchange", table_name="etf_info")
    op.drop_table("etf_info")
