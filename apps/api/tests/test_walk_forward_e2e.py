# ruff: noqa: E501

from __future__ import annotations

import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.dependencies import get_app_config
from vela_api.main import app
from vela_core import load_app_config
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import (
    ETFInfo,
    MarketPrice,
    TradingCalendar,
    WalkForwardRun,
    WalkForwardRunWindow,
)
from vela_core.walk_forward import runner as runner_module

from tests.integration_data import prepare_sqlite_database

_STRATEGY_ID = "Dual_momentum"


def _write_configs(tmp_path: Path) -> tuple[Path, Path]:
    strategy = tmp_path / "strategy.yaml"
    strategy.write_text(
        """strategy_id: Dual_momentum
version: test-v1
type: dual_momentum
universe_config: pool.yaml
rebalance: {frequency: weekly}
parameters:
  momentum: {short_window_days: 20, long_window_days: 80}
  score_weights: {short: 0.4, long: 0.6}
  trend_filter: {moving_average_days: 60, price_relation: above}
  selection: {top_n: 1}
  defense: {assets: [{exchange: SSE, symbol: '510300'}]}
costs: {transaction_cost_bps: 5}
performance: {risk_free_rate: 0.02}
""",
        encoding="utf-8",
    )
    walk = tmp_path / "walk.yaml"
    walk.write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2018-01-02, end_date: 2020-01-02,
  train_years: 1, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1]}]
""",
        encoding="utf-8",
    )
    return strategy, walk


def _seed_market_data(session_factory) -> None:
    sessions: list[date] = []
    current = date(2017, 6, 1)
    while current <= date(2020, 1, 10):
        if current.weekday() < 5:
            sessions.append(current)
        current += timedelta(days=1)
    with session_factory() as session:
        csi_300 = ETFInfo(
            exchange="SSE",
            symbol="510300",
            name="CSI 300 fixture ETF",
            currency="CNY",
            category="risk",
        )
        defensive = ETFInfo(
            exchange="SSE",
            symbol="511010",
            name="Defensive fixture ETF",
            currency="CNY",
            category="defense",
        )
        session.add_all([csi_300, defensive])
        session.flush()
        session.add_all(
            TradingCalendar(trade_date=trade_date, source="e2e-walk-forward-test")
            for trade_date in sessions
        )
        session.add_all(
            price
            for index, trade_date in enumerate(sessions)
            for price in (
                _price(csi_300.id, trade_date, index, Decimal("0.040")),
                _price(defensive.id, trade_date, index, Decimal("0.070")),
            )
        )
        session.commit()


def _price(etf_id: int, trade_date: date, index: int, step: Decimal) -> MarketPrice:
    close = Decimal("100") + step * index + Decimal(index % 7) * Decimal("0.010")
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close,
        high_price=close,
        low_price=close,
        close_price=close,
        factor_hfq=Decimal("1"),
        volume=1000,
    )


def _override_config(monkeypatch: pytest.MonkeyPatch, walk_config_path: Path) -> None:
    config = load_app_config("config/strategy_v1.yaml").model_copy(
        update={"walk_forward_config_path": walk_config_path}
    )
    app.dependency_overrides[get_app_config] = lambda: config


def _poll_until_terminal(client: TestClient, run_id: int, *, timeout_seconds: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f"/api/walk-forwards/{run_id}")
        assert response.status_code == 200
        status = response.json()["run"]["status"]
        if status in ("success", "failed"):
            return response.json()
        time.sleep(0.25)
    raise AssertionError("walk-forward run did not reach a terminal state in time")


def test_e2e_run_trigger_transitions_running_to_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'e2e-success.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_market_data(session_factory)
    _, walk_config = _write_configs(tmp_path)
    _override_config(monkeypatch, walk_config)

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        accepted = client.post("/api/walk-forwards/run")
        assert accepted.status_code == 202
        run_id = accepted.json()["walk_forward_run_id"]
        assert run_id > 0

        detail = _poll_until_terminal(client, run_id)
        assert detail["run"]["status"] == "success"
        assert detail["run"]["error_message"] is None
        assert detail["run"]["finished_at"] is not None
        assert detail["run"]["window_count"] == 1
        assert len(detail["windows"]) == 1
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    with session_factory() as session:
        parent = session.get(WalkForwardRun, run_id)
        assert parent is not None
        assert parent.status == "success"
        assert len(parent.windows) == 1
        assert session.query(WalkForwardRunWindow).count() == 1


def test_e2e_run_trigger_transitions_running_to_failed_without_children(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'e2e-failed.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_market_data(session_factory)
    _, walk_config = _write_configs(tmp_path)
    _override_config(monkeypatch, walk_config)

    # Make every training combination unscorable so the runner raises
    # "no scorable parameter combinations" after the running row is committed.
    def unscorable_backtest(_current_session, **_kwargs) -> SimpleNamespace:
        return SimpleNamespace(status="partial", sharpe_ratio=None, annualized_return=None)

    monkeypatch.setattr(runner_module, "run_backtest", unscorable_backtest)

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        accepted = client.post("/api/walk-forwards/run")
        assert accepted.status_code == 202
        run_id = accepted.json()["walk_forward_run_id"]

        detail = _poll_until_terminal(client, run_id)
        assert detail["run"]["status"] == "failed"
        assert detail["run"]["error_message"] is not None
        assert "no scorable" in detail["run"]["error_message"]
        assert detail["run"]["window_count"] == 0
        assert detail["windows"] == []
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    with session_factory() as session:
        parent = session.get(WalkForwardRun, run_id)
        assert parent is not None
        assert parent.status == "failed"
        assert session.query(WalkForwardRunWindow).count() == 0
