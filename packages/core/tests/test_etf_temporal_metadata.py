from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vela_core import ETFConfig, ETFPoolConfig
from vela_core.models import Base, ETFInfo, MarketPrice, TradingCalendar
from vela_core.walk_forward.config import load_walk_forward_config
from vela_core.walk_forward.preflight import prepare_walk_forward_inputs


def test_etf_configuration_keeps_fund_inception_and_exchange_listing_distinct() -> None:
    configured = ETFConfig(
        exchange="SSE",
        symbol="510300",
        name="CSI 300 ETF",
        inception_date=date(2012, 5, 1),
        listing_date=date(2012, 5, 28),
    )

    assert configured.inception_date == date(2012, 5, 1)
    assert configured.listing_date == date(2012, 5, 28)
    assert configured.inception_date != configured.listing_date


def test_active_etf_configuration_requires_exchange_listing_date() -> None:
    with pytest.raises(ValueError, match="listing_date"):
        ETFPoolConfig(
            pool_id="test_pool",
            version=1,
            provider="test",
            currency="CNY",
            etfs=[
                ETFConfig(
                    exchange="SSE",
                    symbol="510300",
                    name="CSI 300 ETF",
                    is_active=True,
                )
            ],
        )


def test_preflight_does_not_use_first_stored_price_as_listing_boundary(tmp_path: Path) -> None:
    strategy_path = tmp_path / "strategy.yaml"
    strategy_path.write_text(
        """strategy_id: demo
version: v1
type: equal_weight
universe_config: pool.yaml
rebalance: {frequency: weekly}
parameters: {}
costs: {transaction_cost_bps: 10}
performance: {risk_free_rate: 0.02}
""",
        encoding="utf-8",
    )
    (tmp_path / "walk.yaml").write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2020-01-01, end_date: 2020-01-02,
  train_years: 1, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: version, type: choice, values: [v1]}]
""",
        encoding="utf-8",
    )
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'preflight.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add(
            ETFInfo(
                exchange="SSE",
                symbol="510300",
                name="CSI 300 ETF",
                currency="CNY",
                inception_date=date(2010, 1, 1),
                listing_date=None,
                is_active=True,
            )
        )
        session.add_all(
            TradingCalendar(trade_date=item, source="test")
            for item in (date(2020, 1, 2), date(2020, 1, 3))
        )
        session.add(
            MarketPrice(
                etf_id=1,
                trade_date=date(2020, 1, 2),
                open_price=Decimal("1"),
                high_price=Decimal("1"),
                low_price=Decimal("1"),
                close_price=Decimal("1"),
                factor_hfq=Decimal("1"),
            )
        )
        session.commit()

        with pytest.raises(ValueError, match="listing_date.*510300"):
            prepare_walk_forward_inputs(
                session,
                config=load_walk_forward_config(tmp_path / "walk.yaml"),
            )
