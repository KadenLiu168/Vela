from datetime import date

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import DataFetchLog, MarketPrice

from tests.integration_data import (
    ControlledMarketDataProvider,
    add_etf,
    add_market_price,
    daily_price,
    prepare_sqlite_database,
)


def test_market_data_fetch_endpoint_runs_incremental_workflow_with_sqlite(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'market-data.db'}"
    session_factory = prepare_sqlite_database(database_url)
    provider = ControlledMarketDataProvider(
        {"SPY": [daily_price(symbol="SPY", trade_date=date(2026, 6, 18))]}
    )
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        add_market_price(session, etf_id=spy.id, trade_date=date(2026, 6, 17))
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/market-data/fetch?mode=incremental")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "requested_etf_count": 1,
        "rows_fetched": 1,
        "rows_inserted": 1,
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [("SPY", date(2026, 6, 18))]

    with session_factory() as session:
        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()
        log = session.query(DataFetchLog).one()

    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]
    assert log.fetch_mode == "incremental"
    assert log.status == "success"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 1
    assert log.rows_updated == 0


def test_market_data_fetch_endpoint_updates_dashboard_summary(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'market-data-dashboard-loop.db'}"
    session_factory = prepare_sqlite_database(database_url)
    provider = ControlledMarketDataProvider(
        {"SPY": [daily_price(symbol="SPY", trade_date=date(2026, 6, 18))]}
    )
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        add_market_price(session, etf_id=spy.id, trade_date=date(2026, 6, 17))
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider
        client = TestClient(app)

        fetch_response = client.post("/api/market-data/fetch?mode=incremental")
        dashboard_response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert fetch_response.status_code == 200
    assert fetch_response.json() == {
        "status": "success",
        "requested_etf_count": 1,
        "rows_fetched": 1,
        "rows_inserted": 1,
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [("SPY", date(2026, 6, 18))]

    with session_factory() as session:
        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()
        log = session.query(DataFetchLog).one()

    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]
    assert log.fetch_mode == "incremental"
    assert log.status == "success"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 1
    assert log.rows_updated == 0
    assert log.finished_at is not None

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["market_data"] == {
        "price_rows": 2,
        "covered_etfs": 1,
        "earliest_trade_date": "2026-06-17",
        "latest_trade_date": "2026-06-18",
    }
    assert dashboard["recent_fetch_logs"] == [
        {
            "fetch_log_id": log.id,
            "fetch_time": log.finished_at.replace(tzinfo=None).isoformat(),
            "mode": "incremental",
            "status": "success",
            "rows_fetched": 1,
            "rows_inserted": 1,
            "rows_updated": 0,
            "error_summary": None,
        }
    ]


def test_market_data_fetch_endpoint_runs_full_workflow(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'full-market-data.db'}"
    session_factory = prepare_sqlite_database(database_url)
    provider = ControlledMarketDataProvider(
        {"SPY": [daily_price(symbol="SPY", trade_date=date(2026, 6, 18))]}
    )
    with session_factory() as session:
        add_etf(session, symbol="SPY")
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/market-data/fetch?mode=full")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "requested_etf_count": 1,
        "rows_fetched": 1,
        "rows_inserted": 1,
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [("SPY", None)]


def test_market_data_fetch_endpoint_rejects_invalid_mode(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-market-data.db'}"
    provider = ControlledMarketDataProvider({})

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/market-data/fetch?mode=recent")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert provider.requests == []
