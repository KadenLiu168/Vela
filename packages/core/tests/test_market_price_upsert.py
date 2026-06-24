from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import upsert_market_prices
from vela_core.models import Base, ETFInfo, MarketPrice


def test_upsert_market_prices_inserts_new_row() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")

        result = upsert_market_prices(
            session,
            [_market_price(etf_id=etf.id, close_price=Decimal("500.00"))],
        )
        session.commit()

        prices = session.query(MarketPrice).all()

        assert result.rows_inserted == 1
        assert result.rows_updated == 0
        assert len(prices) == 1
        assert prices[0].close_price == Decimal("500.000000")


def test_upsert_market_prices_updates_existing_row_without_duplicate() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        upsert_market_prices(
            session,
            [_market_price(etf_id=etf.id, close_price=Decimal("500.00"), volume=1000)],
        )
        session.commit()

        result = upsert_market_prices(
            session,
            [
                _market_price(
                    etf_id=etf.id,
                    close_price=Decimal("501.00"),
                    adjusted_close=Decimal("500.50"),
                    volume=2000,
                )
            ],
        )
        session.commit()

        prices = session.query(MarketPrice).all()

        assert result.rows_inserted == 0
        assert result.rows_updated == 1
        assert len(prices) == 1
        assert prices[0].close_price == Decimal("501.000000")
        assert prices[0].adjusted_close == Decimal("500.500000")
        assert prices[0].volume == 2000


def test_upsert_market_prices_stores_different_etfs_on_same_trade_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")

        result = upsert_market_prices(
            session,
            [
                _market_price(etf_id=spy.id, close_price=Decimal("500.00")),
                _market_price(etf_id=qqq.id, close_price=Decimal("420.00")),
            ],
        )
        session.commit()

        assert result.rows_inserted == 2
        assert result.rows_updated == 0
        assert session.query(MarketPrice).count() == 2


def test_upsert_market_prices_returns_zero_counts_for_empty_input() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = upsert_market_prices(session, [])

        assert result.rows_inserted == 0
        assert result.rows_updated == 0
        assert session.query(MarketPrice).count() == 0


def test_upsert_market_prices_uses_last_value_for_duplicate_batch_keys() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")

        result = upsert_market_prices(
            session,
            [
                _market_price(etf_id=etf.id, close_price=Decimal("500.00"), volume=1000),
                _market_price(etf_id=etf.id, close_price=Decimal("501.00"), volume=2000),
            ],
        )
        session.commit()

        prices = session.query(MarketPrice).all()

        assert result.rows_inserted == 1
        assert result.rows_updated == 0
        assert len(prices) == 1
        assert prices[0].close_price == Decimal("501.000000")
        assert prices[0].volume == 2000


def test_upsert_market_prices_deduplicates_repeated_etf_trade_date_writes() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        upsert_market_prices(
            session,
            [_market_price(etf_id=etf.id, close_price=Decimal("500.00"), volume=1000)],
        )
        session.commit()

        result = upsert_market_prices(
            session,
            [
                _market_price(etf_id=etf.id, close_price=Decimal("501.00"), volume=2000),
                _market_price(etf_id=etf.id, close_price=Decimal("502.00"), volume=3000),
            ],
        )
        session.commit()

        price = session.query(MarketPrice).filter_by(
            etf_id=etf.id,
            trade_date=date(2026, 6, 18),
        ).one()

        assert result.rows_inserted == 0
        assert result.rows_updated == 1
        assert session.query(MarketPrice).count() == 1
        assert price.close_price == Decimal("502.000000")
        assert price.volume == 3000


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
    adjusted_close: Decimal | None = None,
    volume: int | None = 1000,
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=date(2026, 6, 18),
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=close_price,
        adjusted_close=adjusted_close,
        volume=volume,
    )
