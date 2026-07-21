from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import MarketPrice

from tests.integration_data import add_etf, market_price, prepare_sqlite_database

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_etf_prices_endpoint_returns_forward_adjusted_series_ordered_ascending(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'etf-prices.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        session.add_all(
            [
                _adjusted_market_price(
                    etf_id=spy.id,
                    trade_date=date(2026, 6, 22),
                    close_price=Decimal("100.000000"),
                    factor_hfq=Decimal("1"),
                ),
                _adjusted_market_price(
                    etf_id=spy.id,
                    trade_date=date(2026, 6, 23),
                    close_price=Decimal("80.000000"),
                    factor_hfq=Decimal("1.500000000000"),
                ),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/etfs/{spy.id}/prices?range=max")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["etf"] == {
        "id": spy.id,
        "exchange": "NYSEARCA",
        "symbol": "SPY",
        "name": "SPY ETF",
    }
    points = body["points"]
    assert [point["trade_date"] for point in points] == ["2026-06-22", "2026-06-23"]
    assert Decimal(points[0]["price"]) == Decimal("100.000000") / Decimal("1.500000000000")
    assert Decimal(points[1]["price"]) == Decimal("80.000000")


def test_etf_prices_endpoint_resolves_range_window_anchored_at_latest_trade_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'etf-prices-window.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        session.add_all(
            [
                market_price(etf_id=spy.id, trade_date=date(2025, 1, 10)),
                market_price(etf_id=spy.id, trade_date=date(2026, 4, 15)),
                market_price(etf_id=spy.id, trade_date=date(2026, 6, 23)),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        three_month = client.get(f"/api/etfs/{spy.id}/prices?range=3m")
        maximum = client.get(f"/api/etfs/{spy.id}/prices?range=max")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert three_month.status_code == 200
    assert [point["trade_date"] for point in three_month.json()["points"]] == [
        "2026-04-15",
        "2026-06-23",
    ]
    assert maximum.status_code == 200
    assert [point["trade_date"] for point in maximum.json()["points"]] == [
        "2025-01-10",
        "2026-04-15",
        "2026-06-23",
    ]


def test_etf_prices_endpoint_returns_empty_points_for_etf_without_prices(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'etf-prices-empty.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/etfs/{spy.id}/prices?range=1y")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["etf"]["id"] == spy.id
    assert body["points"] == []


def test_etf_prices_endpoint_returns_404_for_unknown_etf(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'etf-prices-unknown.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get("/api/etfs/999/prices?range=1y")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "not_found",
        "category": "not_found",
        "message": "ETF not found",
    }


def test_etf_prices_endpoint_returns_422_for_invalid_range(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'etf-prices-invalid.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        session.add(market_price(etf_id=spy.id, trade_date=date(2026, 6, 23)))
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/etfs/{spy.id}/prices?range=2y")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "validation_error",
        "category": "validation",
        "message": "Request validation failed",
    }


def _adjusted_market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal,
    factor_hfq: Decimal,
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        factor_hfq=factor_hfq,
        volume=1000,
    )
