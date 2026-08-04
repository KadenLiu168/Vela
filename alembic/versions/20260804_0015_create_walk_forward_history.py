"""Create persisted Walk-forward history.

Revision ID: 20260804_0015
Revises: 20260804_0014
Create Date: 2026-08-04
"""

import sqlalchemy as sa

from alembic import op

revision = "20260804_0015"
down_revision = "20260804_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "walk_forward_run",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strategy_id", sa.String(length=128), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("window_count", sa.Integer(), nullable=False),
        sa.Column("walk_forward_config_json", sa.JSON(), nullable=False),
        sa.Column("base_strategy_config_json", sa.JSON(), nullable=False),
        sa.Column("provenance_version", sa.String(length=64), nullable=False),
        sa.Column("config_checksum", sa.String(length=64), nullable=False),
        sa.Column("input_data_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("input_data_checksum", sa.String(length=64), nullable=False),
        sa.Column("evidence_version", sa.String(length=64), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "window_count >= 0", name="ck_walk_forward_run_window_count_nonnegative"
        ),
    )
    op.create_index(
        "ix_walk_forward_run_strategy_finished_id",
        "walk_forward_run",
        ["strategy_id", "finished_at", "id"],
    )
    op.create_table(
        "walk_forward_run_window",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("walk_forward_run_id", sa.Integer(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("train_start", sa.Date(), nullable=False),
        sa.Column("train_end", sa.Date(), nullable=False),
        sa.Column("test_start", sa.Date(), nullable=False),
        sa.Column("test_end", sa.Date(), nullable=False),
        sa.Column("oos_version", sa.String(length=64), nullable=False),
        sa.Column("selected_parameters_json", sa.JSON(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("skip_reason_counts_json", sa.JSON(), nullable=False),
        sa.Column("train_sharpe", sa.Numeric(18, 6), nullable=True),
        sa.Column("oos_backtest_run_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "candidate_count >= 0", name="ck_walk_forward_window_candidate_nonnegative"
        ),
        sa.CheckConstraint(
            "eligible_count >= 0", name="ck_walk_forward_window_eligible_nonnegative"
        ),
        sa.CheckConstraint("skipped_count >= 0", name="ck_walk_forward_window_skipped_nonnegative"),
        sa.CheckConstraint(
            "candidate_count = eligible_count + skipped_count",
            name="ck_walk_forward_window_counts_reconciled",
        ),
        sa.ForeignKeyConstraint(["walk_forward_run_id"], ["walk_forward_run.id"]),
        sa.ForeignKeyConstraint(["oos_backtest_run_id"], ["backtest_run.id"]),
        sa.UniqueConstraint(
            "walk_forward_run_id", "ordinal", name="uq_walk_forward_window_run_ordinal"
        ),
        sa.UniqueConstraint("oos_backtest_run_id", name="uq_walk_forward_window_oos_run"),
    )


def downgrade() -> None:
    op.drop_table("walk_forward_run_window")
    op.drop_index("ix_walk_forward_run_strategy_finished_id", table_name="walk_forward_run")
    op.drop_table("walk_forward_run")
