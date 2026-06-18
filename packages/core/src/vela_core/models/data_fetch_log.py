from datetime import date, datetime
from typing import ClassVar

from sqlalchemy import Date, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from vela_core.models.base import Base


class DataFetchLog(Base):
    __tablename__ = "data_fetch_log"
    __table_args__ = (
        Index("ix_data_fetch_log_source_status_started_at", "source", "status", "started_at"),
        Index(
            "ix_data_fetch_log_target_mode_range",
            "target_type",
            "fetch_mode",
            "range_start",
            "range_end",
        ),
    )

    STATUSES: ClassVar[tuple[str, ...]] = ("running", "success", "failed", "partial")
    FETCH_MODES: ClassVar[tuple[str, ...]] = ("full", "incremental")

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    fetch_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    range_start: Mapped[date | None] = mapped_column(Date)
    range_end: Mapped[date | None] = mapped_column(Date)
    requested_symbols: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rows_fetched: Mapped[int | None] = mapped_column(Integer)
    rows_inserted: Mapped[int | None] = mapped_column(Integer)
    rows_updated: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
