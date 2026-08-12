"""add ETF listing dates and authoritative session status reference data

Revision ID: 20260811_0020
Revises: 20260810_0019
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260811_0020"
down_revision: str | None = "20260810_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("etf_info", sa.Column("listing_date", sa.Date(), nullable=True))
    op.create_table(
        "etf_session_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("etf_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=False),
        sa.Column("source_uri", sa.String(length=2048), nullable=False),
        sa.Column("source_published_date", sa.Date(), nullable=False),
        sa.Column("share_ratio", sa.Numeric(precision=18, scale=10), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('full_day_suspension', 'corporate_action_halt')",
            name="ck_etf_session_status_status",
        ),
        sa.CheckConstraint(
            "share_ratio IS NULL OR share_ratio > 0",
            name="ck_etf_session_status_share_ratio_positive",
        ),
        sa.CheckConstraint("length(reason) BETWEEN 1 AND 128", name="ck_etf_session_status_reason"),
        sa.CheckConstraint(
            "length(source_uri) BETWEEN 1 AND 2048",
            name="ck_etf_session_status_source_uri",
        ),
        sa.ForeignKeyConstraint(["etf_id"], ["etf_info.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("etf_id", "trade_date", name="uq_etf_session_status_etf_trade_date"),
    )
    op.create_index(
        "ix_etf_session_status_etf_trade_date",
        "etf_session_status",
        ["etf_id", "trade_date"],
    )
    op.create_index("ix_etf_session_status_trade_date", "etf_session_status", ["trade_date"])


def downgrade() -> None:
    op.drop_index("ix_etf_session_status_trade_date", table_name="etf_session_status")
    op.drop_index("ix_etf_session_status_etf_trade_date", table_name="etf_session_status")
    op.drop_table("etf_session_status")
    op.drop_column("etf_info", "listing_date")
