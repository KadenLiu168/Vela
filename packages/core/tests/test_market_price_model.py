from datetime import date
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy import Table, UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from vela_core.models import Base, ETFInfo, MarketPrice


def test_market_price_table_has_required_columns() -> None:
    table = cast(Table, MarketPrice.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "etf_id",
        "trade_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "factor_hfq",
        "volume",
        "created_at",
        "updated_at",
    } <= columns
    assert "adjusted_close" not in columns
    assert table.columns["factor_hfq"].nullable is False


def test_market_price_references_etf_info() -> None:
    table = cast(Table, MarketPrice.__table__)
    foreign_keys = table.columns["etf_id"].foreign_keys

    assert any(foreign_key.column.table.name == "etf_info" for foreign_key in foreign_keys)


def test_market_price_has_etf_trade_date_unique_constraint() -> None:
    table = cast(Table, MarketPrice.__table__)
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        {column.name for column in constraint.columns} == {"etf_id", "trade_date"}
        for constraint in unique_constraints
    )


def test_market_price_rejects_duplicate_etf_trade_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        session.add(_market_price(etf_id=etf.id, close_price=Decimal("500.00")))
        session.commit()

        session.add(_market_price(etf_id=etf.id, close_price=Decimal("501.00")))
        with pytest.raises(IntegrityError):
            session.commit()


def test_market_price_allows_same_trade_date_for_different_etfs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        session.add_all(
            [
                _market_price(etf_id=spy.id, close_price=Decimal("500.00")),
                _market_price(etf_id=qqq.id, close_price=Decimal("420.00")),
            ]
        )
        session.commit()

        assert session.query(MarketPrice).count() == 2


def test_market_price_has_lookup_indexes() -> None:
    table = cast(Table, MarketPrice.__table__)
    indexed_columns = {tuple(column.name for column in index.columns) for index in table.indexes}

    assert ("etf_id", "trade_date") in indexed_columns
    assert ("trade_date",) in indexed_columns


def test_market_price_has_no_strategy_price_attribute() -> None:
    market_price = _market_price(
        etf_id=1,
        close_price=Decimal("100.00"),
        factor_hfq=Decimal("1.25"),
    )

    assert not hasattr(market_price, "strategy_price")
    with pytest.raises(AttributeError):
        _ = market_price.strategy_price


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _add_etf(session: Session, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf


def _market_price(
    *,
    etf_id: int,
    close_price: Decimal,
    factor_hfq: Decimal = Decimal("1"),
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=date(2026, 6, 18),
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=close_price,
        factor_hfq=factor_hfq,
        volume=1000,
    )
