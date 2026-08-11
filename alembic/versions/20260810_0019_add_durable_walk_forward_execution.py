"""Add durable Walk-forward execution lifecycle.

Revision ID: 20260810_0019
Revises: 20260807_0018
Create Date: 2026-08-10
"""

import sqlalchemy as sa

from alembic import op

revision = "20260810_0019"
down_revision = "20260807_0018"
branch_labels = None
depends_on = None

_MIGRATION_INTERRUPTION = "migration_interrupted: legacy running claim was not durable"


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE walk_forward_run "
            "SET status = 'failed', "
            "finished_at = COALESCE(finished_at, CURRENT_TIMESTAMP), "
            "error_message = :error_message "
            "WHERE status = 'running'"
        ).bindparams(error_message=_MIGRATION_INTERRUPTION)
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("attempt_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("worker_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "walk_forward_run",
        sa.Column("claim_token", sa.String(length=64), nullable=True),
    )
    op.execute(sa.text("UPDATE walk_forward_run SET attempt_count = 0"))

    with op.batch_alter_table("walk_forward_run") as batch_op:
        batch_op.drop_constraint("ck_walk_forward_run_status", type_="check")
        batch_op.create_check_constraint(
            "ck_walk_forward_run_status",
            "status IN ('queued','running','success','failed')",
        )
        batch_op.create_check_constraint(
            "ck_walk_forward_run_attempt_count_nonnegative",
            "attempt_count >= 0",
        )
        batch_op.alter_column(
            "attempt_count",
            existing_type=sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        )

    op.execute(
        "CREATE UNIQUE INDEX uq_walk_forward_run_active_strategy "
        "ON walk_forward_run(strategy_id) "
        "WHERE status IN ('queued','running')"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_walk_forward_run_sqlite_running "
        "ON walk_forward_run ((1)) WHERE status = 'running'"
    )


def downgrade() -> None:
    active_count = (
        op.get_bind()
        .execute(
            sa.text("SELECT COUNT(*) FROM walk_forward_run WHERE status IN ('queued','running')")
        )
        .scalar_one()
    )
    if active_count:
        raise RuntimeError("cannot downgrade while a Walk-forward execution is active")

    op.execute("DROP INDEX uq_walk_forward_run_sqlite_running")
    op.execute("DROP INDEX uq_walk_forward_run_active_strategy")
    with op.batch_alter_table("walk_forward_run") as batch_op:
        batch_op.drop_constraint("ck_walk_forward_run_attempt_count_nonnegative", type_="check")
        batch_op.drop_constraint("ck_walk_forward_run_status", type_="check")
        batch_op.create_check_constraint(
            "ck_walk_forward_run_status",
            "status IN ('running','success','failed')",
        )
        batch_op.drop_column("claim_token")
        batch_op.drop_column("worker_id")
        batch_op.drop_column("lease_expires_at")
        batch_op.drop_column("heartbeat_at")
        batch_op.drop_column("claimed_at")
        batch_op.drop_column("attempt_count")
