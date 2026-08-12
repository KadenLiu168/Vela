from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import ETFConfig, ETFPoolConfig, sync_etf_pool_to_db
from vela_core.models import Base, ETFInfo


def test_sync_etf_pool_inserts_configured_etfs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = sync_etf_pool_to_db(session, _pool())
        session.commit()

        etfs = session.query(ETFInfo).order_by(ETFInfo.symbol).all()

        assert result.pool_id == "test_pool"
        assert result.total_etfs == 2
        assert result.inserted_count == 2
        assert result.updated_count == 0
        assert result.unchanged_count == 0
        assert [(etf.exchange, etf.symbol, etf.name, etf.currency) for etf in etfs] == [
            ("SZSE", "159915", "创业板ETF", "CNY"),
            ("SSE", "510300", "沪深300ETF", "CNY"),
        ]
        assert etfs[0].inception_date == date(2011, 9, 20)
        assert etfs[0].listing_date == date(2011, 12, 9)
        assert etfs[1].inception_date == date(2012, 5, 1)
        assert etfs[1].listing_date == date(2012, 5, 28)


def test_sync_etf_pool_reports_unchanged_on_second_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        sync_etf_pool_to_db(session, _pool())
        session.commit()

        result = sync_etf_pool_to_db(session, _pool())
        session.commit()

        assert result.inserted_count == 0
        assert result.updated_count == 0
        assert result.unchanged_count == 2
        assert session.query(ETFInfo).count() == 2


def test_sync_etf_pool_updates_yaml_owned_fields() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            ETFInfo(
                exchange="SSE",
                symbol="510300",
                name="Old name",
                currency="USD",
                category="old_category",
                is_active=False,
            )
        )
        session.commit()

        result = sync_etf_pool_to_db(session, _pool())
        session.commit()

        etf = session.query(ETFInfo).filter_by(exchange="SSE", symbol="510300").one()

        assert result.inserted_count == 1
        assert result.updated_count == 1
        assert result.unchanged_count == 0
        assert etf.name == "沪深300ETF"
        assert etf.currency == "CNY"
        assert etf.category == "equity_cn_large"
        assert etf.is_active is True


def test_sync_etf_pool_updates_inception_and_listing_dates_independently() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            ETFInfo(
                exchange="SSE",
                symbol="510300",
                name="沪深300ETF",
                currency="CNY",
                inception_date=date(2012, 5, 1),
                listing_date=date(2012, 5, 28),
                is_active=True,
            )
        )
        session.commit()

        updated_pool = _pool().model_copy(
            update={
                "etfs": [
                    _pool()
                    .etfs[0]
                    .model_copy(
                        update={
                            "inception_date": date(2012, 5, 2),
                            "listing_date": date(2012, 5, 29),
                        }
                    ),
                    _pool().etfs[1],
                ]
            }
        )
        result = sync_etf_pool_to_db(session, updated_pool)
        session.commit()

        etf = session.query(ETFInfo).filter_by(symbol="510300").one()
        assert result.updated_count == 1
        assert etf.inception_date == date(2012, 5, 2)
        assert etf.listing_date == date(2012, 5, 29)


def test_sync_etf_pool_preserves_rows_outside_configured_pool() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            ETFInfo(
                exchange="SSE",
                symbol="588000",
                name="科创50ETF",
                currency="CNY",
                category="existing",
                is_active=True,
            )
        )
        session.commit()

        sync_etf_pool_to_db(session, _pool())
        session.commit()

        out_of_pool = session.query(ETFInfo).filter_by(exchange="SSE", symbol="588000").one()

        assert out_of_pool.name == "科创50ETF"
        assert out_of_pool.category == "existing"
        assert out_of_pool.is_active is True
        assert session.query(ETFInfo).count() == 3


def _pool() -> ETFPoolConfig:
    return ETFPoolConfig(
        pool_id="test_pool",
        version=1,
        provider="tencent",
        currency="CNY",
        etfs=[
            ETFConfig(
                exchange="SSE",
                symbol="510300",
                name="沪深300ETF",
                category="equity_cn_large",
                is_active=True,
                inception_date=date(2012, 5, 1),
                listing_date=date(2012, 5, 28),
            ),
            ETFConfig(
                exchange="SZSE",
                symbol="159915",
                name="创业板ETF",
                category="equity_cn_growth",
                is_active=True,
                inception_date=date(2011, 9, 20),
                listing_date=date(2011, 12, 9),
            ),
        ],
    )


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
