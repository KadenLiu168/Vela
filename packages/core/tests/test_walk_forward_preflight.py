from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, ETFInfo, MarketPrice, TradingCalendar
from vela_core.walk_forward import preflight as preflight_module
from vela_core.walk_forward.config import load_walk_forward_config
from vela_core.walk_forward.preflight import prepare_walk_forward_inputs


def _config(tmp_path: Path) -> Path:
    strategy = tmp_path / "strategy.yaml"
    strategy.write_text(
        """strategy_id: demo
version: v1
type: equal_weight
universe_config: pool.yaml
rebalance: {frequency: weekly}
parameters: {}
costs: {transaction_cost_bps: 10}
performance: {risk_free_rate: 0.02}
"""
    )
    path = tmp_path / "walk.yaml"
    path.write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2020-01-01, end_date: 2021-12-31,
  train_years: 1, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: version, type: choice, values: [v1]}]
"""
    )
    return path


def _seed(session) -> None:
    session.add(
        ETFInfo(
            id=1,
            exchange="SSE",
            symbol="510300",
            name="CSI 300",
            currency="CNY",
            inception_date=date(2019, 1, 1),
            is_active=True,
        )
    )
    session.add(
        ETFInfo(
            id=2,
            exchange="SSE",
            symbol="159999",
            name="Post-window ETF",
            currency="CNY",
            inception_date=date(2022, 1, 1),
            is_active=True,
        )
    )
    dates = [date(2020, 1, 2), date(2020, 12, 31), date(2021, 1, 4), date(2021, 12, 31)]
    session.add_all(
        [TradingCalendar(trade_date=item, source="test") for item in [*dates, date(2022, 1, 4)]]
    )
    session.add_all(
        MarketPrice(
            etf_id=1,
            trade_date=item,
            open_price=Decimal("1"),
            high_price=Decimal("1"),
            low_price=Decimal("1"),
            close_price=Decimal("1.2"),
            factor_hfq=Decimal("1"),
        )
        for item in [*dates, date(2020, 6, 1), date(2022, 1, 1)]
    )
    session.commit()


def test_preflight_uses_calendar_axis_and_builds_compact_manifest(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'preflight.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _seed(session)
        config = load_walk_forward_config(_config(tmp_path))

        prepared = prepare_walk_forward_inputs(session, config=config)

    assert [window.test_start for window in prepared.windows] == [date(2021, 1, 4)]
    assert set(prepared.manifest) == {
        "version",
        "earliest_required_session",
        "configured_end_date",
        "following_session",
        "official_sessions",
        "active_etfs",
        "loaded_price_row_count",
        "first_loaded_price_date",
        "last_loaded_price_date",
    }
    assert prepared.manifest["following_session"] == "2022-01-04"
    assert prepared.manifest["active_etfs"][0]["loaded_price_row_count"] == 5
    assert prepared.manifest["active_etfs"][1]["loaded_price_row_count"] == 0
    assert prepared.maximum_lookback_days == 0
    assert "close_price" not in repr(prepared.manifest)
    assert prepared.input_data_checksum == prepared.input_data_checksum.lower()


def test_preflight_fails_on_missing_official_price_before_source_output(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'missing.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _seed(session)
        session.query(MarketPrice).filter(MarketPrice.trade_date == date(2021, 12, 31)).delete()
        session.commit()
        with pytest.raises(ValueError, match="missing required market price"):
            prepare_walk_forward_inputs(session, config=load_walk_forward_config(_config(tmp_path)))


def test_preflight_rejects_no_valid_candidates_and_negative_declared_lookback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _config(tmp_path)
    invalid_path = tmp_path / "no-valid-candidate.yaml"
    invalid_path.write_text(
        config_path.read_text().replace("name: version", "name: parameters.invalid"),
    )
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'candidate-validation.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        with pytest.raises(ValueError, match="no valid parameter combinations"):
            prepare_walk_forward_inputs(session, config=load_walk_forward_config(invalid_path))

        class NegativeLookbackStrategy:
            def lookback_days(self) -> int:
                return -1

        monkeypatch.setattr(
            preflight_module,
            "resolve_strategy",
            lambda _config: NegativeLookbackStrategy(),
        )
        with pytest.raises(ValueError, match="lookback_days must be non-negative"):
            prepare_walk_forward_inputs(session, config=load_walk_forward_config(config_path))
