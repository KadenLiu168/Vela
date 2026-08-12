from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from vela_core.models.base import Base


class ETFInfo(Base):
    __tablename__ = "etf_info"
    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_etf_info_exchange_symbol"),
        Index("ix_etf_info_symbol", "symbol"),
        Index("ix_etf_info_exchange", "exchange"),
        Index("ix_etf_info_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(128))
    inception_date: Mapped[date | None] = mapped_column(Date)
    listing_date: Mapped[date | None] = mapped_column(Date)
    expense_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
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
