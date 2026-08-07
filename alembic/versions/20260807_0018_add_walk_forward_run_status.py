"""Add Walk-forward run status and error message.

Revision ID: 20260807_0018
Revises: 20260806_0017
Create Date: 2026-08-07
"""

import sqlalchemy as sa

from alembic import op

revision = "20260807_0018"
down_revision = "20260806_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite cannot add a NOT NULL column without a server default, so add the
    # column as nullable, backfill every existing row (pre-Change rows were
    # persisted only after successful completion), then enforce NOT NULL.
    op.add_column(
        "walk_forward_run",
        sa.Column("status", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.execute("UPDATE walk_forward_run SET status = 'success' WHERE status IS NULL")
    # Batch mode rebuilds the table so the NOT NULL / CHECK changes apply on
    # SQLite while preserving existing rows and the pre-existing window-count
    # check constraint.
    with op.batch_alter_table("walk_forward_run") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=16),
            nullable=False,
        )
        batch_op.alter_column(
            "finished_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
        )
        batch_op.create_check_constraint(
            "ck_walk_forward_run_status",
            "status IN ('running','success','failed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("walk_forward_run") as batch_op:
        batch_op.drop_constraint("ck_walk_forward_run_status", type_="check")
        batch_op.alter_column(
            "finished_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )
        batch_op.drop_column("status")
        batch_op.drop_column("error_message")
