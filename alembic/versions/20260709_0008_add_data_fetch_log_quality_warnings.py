"""add quality_warnings column to data_fetch_log

Revision ID: 20260709_0008
Revises: 20260708_0007
Create Date: 2026-07-09

This revision adds a nullable ``quality_warnings`` TEXT column to
``data_fetch_log``. The column stores a JSON envelope of data-quality soft
signals (e.g. duplicate trade dates detected in a fetch batch) and is kept
separate from the hard-failure ``error_message`` column. Existing rows are
unaffected: ``NULL`` means "not checked / no warnings".
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260709_0008"
down_revision: str | None = "20260708_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "data_fetch_log",
        sa.Column("quality_warnings", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("data_fetch_log", "quality_warnings")
