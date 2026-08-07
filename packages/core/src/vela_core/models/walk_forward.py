from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vela_core.models.base import Base

if TYPE_CHECKING:
    from vela_core.models.backtest import BacktestRun


class WalkForwardRun(Base):
    __tablename__ = "walk_forward_run"
    __table_args__ = (
        CheckConstraint("window_count >= 0", name="ck_walk_forward_run_window_count_nonnegative"),
        CheckConstraint(
            "status IN ('running','success','failed')",
            name="ck_walk_forward_run_status",
        ),
        Index(
            "ix_walk_forward_run_strategy_finished_id",
            "strategy_id",
            "finished_at",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    window_count: Mapped[int] = mapped_column(Integer, nullable=False)
    walk_forward_config_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    base_strategy_config_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    provenance_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    input_data_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    input_data_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    windows: Mapped[list[WalkForwardRunWindow]] = relationship(
        back_populates="walk_forward_run",
        order_by=lambda: (WalkForwardRunWindow.ordinal, WalkForwardRunWindow.id),
    )


class WalkForwardRunWindow(Base):
    __tablename__ = "walk_forward_run_window"
    __table_args__ = (
        CheckConstraint(
            "candidate_count >= 0", name="ck_walk_forward_window_candidate_nonnegative"
        ),
        CheckConstraint("eligible_count >= 0", name="ck_walk_forward_window_eligible_nonnegative"),
        CheckConstraint("skipped_count >= 0", name="ck_walk_forward_window_skipped_nonnegative"),
        CheckConstraint(
            "candidate_count = eligible_count + skipped_count",
            name="ck_walk_forward_window_counts_reconciled",
        ),
        UniqueConstraint(
            "walk_forward_run_id", "ordinal", name="uq_walk_forward_window_run_ordinal"
        ),
        UniqueConstraint("oos_backtest_run_id", name="uq_walk_forward_window_oos_run"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    walk_forward_run_id: Mapped[int] = mapped_column(
        ForeignKey("walk_forward_run.id"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    train_start: Mapped[date] = mapped_column(Date, nullable=False)
    train_end: Mapped[date] = mapped_column(Date, nullable=False)
    test_start: Mapped[date] = mapped_column(Date, nullable=False)
    test_end: Mapped[date] = mapped_column(Date, nullable=False)
    oos_version: Mapped[str] = mapped_column(String(64), nullable=False)
    selected_parameters_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    eligible_count: Mapped[int] = mapped_column(Integer, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False)
    skip_reason_counts_json: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    train_sharpe: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    oos_backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_run.id"), nullable=False)
    walk_forward_run: Mapped[WalkForwardRun] = relationship(back_populates="windows")
    oos_backtest_run: Mapped[BacktestRun] = relationship()
