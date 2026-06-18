from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from vela_core.models.base import Base


class MarketPrice(Base):
    __tablename__ = "market_price"
    __table_args__ = (
        UniqueConstraint("etf_id", "trade_date", name="uq_market_price_etf_trade_date"),
        Index("ix_market_price_etf_trade_date", "etf_id", "trade_date"),
        Index("ix_market_price_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    etf_id: Mapped[int] = mapped_column(ForeignKey("etf_info.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volume: Mapped[int | None] = mapped_column(BigInteger)
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

    @property
    def strategy_price(self) -> Decimal:
        return self.adjusted_close if self.adjusted_close is not None else self.close_price
