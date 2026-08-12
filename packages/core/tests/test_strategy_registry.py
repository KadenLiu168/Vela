from datetime import date
from decimal import Decimal

import pytest
import vela_core.strategies.dual_momentum as dual_momentum
import vela_core.strategy_signal_generation as generation
from vela_core.models import ETFInfo, MarketPrice
from vela_core.momentum_scoring import MomentumScore
from vela_core.strategies.dual_momentum import DualMomentumStrategy
from vela_core.strategies.equal_weight import EqualWeightStrategy
from vela_core.strategies.registry import STRATEGY_FACTORIES, resolve_strategy
from vela_core.strategies.types import StrategyGenerationError
from vela_core.strategy_config import validate_strategy_config
from vela_core.trend_filter import TrendFilterResult


def test_registry_binds_validated_variant_parameters() -> None:
    dual = resolve_strategy(_dual_config())
    equal = resolve_strategy(_equal_config())

    assert isinstance(dual, DualMomentumStrategy)
    assert dual.lookback_days() == 126
    assert isinstance(equal, EqualWeightStrategy)
    assert equal.lookback_days() == 0


def test_registry_rejects_unsupported_direct_type() -> None:
    config = _equal_config()
    object.__setattr__(config, "type", "unknown")

    with pytest.raises(ValueError, match="Unsupported strategy type: unknown") as exc_info:
        resolve_strategy(config)

    assert type(exc_info.value).__module__ == "vela_core.strategies.registry"


def test_registry_rejects_runtime_factory_mutation() -> None:
    with pytest.raises(TypeError):
        STRATEGY_FACTORIES["runtime_injected"] = lambda config: resolve_strategy(config)  # type: ignore[index]


def test_equal_weight_has_deterministic_uniform_positions() -> None:
    positions = resolve_strategy(_equal_config()).generate_signal(
        signal_date=date(2026, 1, 1),
        price_panel={},
        active_etfs=[_etf(2, "B"), _etf(1, "A")],
    )

    assert [(p.etf_id, p.rank, p.score, p.target_weight) for p in positions] == [
        (1, None, None, Decimal("0.5")),
        (2, None, None, Decimal("0.5")),
    ]


def test_equal_weight_uses_shared_live_and_historical_generation() -> None:
    active_etfs = [_etf(2, "B"), _etf(1, "A")]
    live = generation.generate_strategy_signal(
        signal_date=date(2026, 1, 1),
        config=_equal_config(),
        price_panel={},
        active_etfs=active_etfs,
    )
    historical = generation.generate_historical_strategy_signals(
        historical_trading_dates=[date(2026, 1, 1), date(2026, 1, 8)],
        config=_equal_config(),
        price_panel={},
        active_etfs=active_etfs,
    )

    assert live.status == "success"
    assert [position.etf_id for position in live.positions] == [1, 2]
    assert [result.status for result in historical] == ["success", "success"]
    assert (
        generation.generate_strategy_signal(
            signal_date=date(2026, 1, 1),
            config=_equal_config(),
            price_panel={},
            active_etfs=[],
        ).status
        == "failed"
    )


def test_historical_generation_hides_future_prices_from_bound_strategy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_date = date(2026, 1, 1)
    second_date = date(2026, 1, 8)
    observed_dates: list[tuple[date, list[date]]] = []

    class InspectingStrategy:
        def lookback_days(self) -> int:
            return 0

        def generate_signal(self, *, signal_date, price_panel, active_etfs):
            observed_dates.append(
                (signal_date, [price.trade_date for price in price_panel[active_etfs[0].id]])
            )
            return []

    monkeypatch.setattr(generation, "resolve_strategy", lambda config: InspectingStrategy())
    generation.generate_historical_strategy_signals(
        historical_trading_dates=[first_date, second_date],
        config=_equal_config(),
        price_panel={
            1: [
                _price(1, first_date),
                _price(1, second_date),
            ]
        },
        active_etfs=[_etf(1, "A")],
    )

    assert observed_dates == [
        (first_date, [first_date]),
        (second_date, [second_date]),
    ]


def test_historical_generation_resolves_once_and_bounds_each_strategy_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start = date(2026, 1, 1)
    trading_dates = [start.fromordinal(start.toordinal() + offset) for offset in range(15)]
    observed: list[tuple[date, list[date]]] = []
    resolutions = 0

    class InspectingStrategy:
        def lookback_days(self) -> int:
            return 2

        def generate_signal(self, *, signal_date, price_panel, active_etfs):
            observed.append((signal_date, [price.trade_date for price in price_panel[1]]))
            return []

    def _resolve(config):
        nonlocal resolutions
        resolutions += 1
        return InspectingStrategy()

    monkeypatch.setattr(generation, "resolve_strategy", _resolve)
    results = generation.generate_historical_strategy_signals(
        historical_trading_dates=trading_dates,
        config=_equal_config(),
        price_panel={1: [_price(1, trade_date) for trade_date in trading_dates]},
        active_etfs=[_etf(1, "A")],
    )

    assert [result.signal_date for result in results] == [
        date(2026, 1, 4),
        date(2026, 1, 11),
        date(2026, 1, 15),
    ]
    assert resolutions == 1
    assert observed == [
        (date(2026, 1, 4), [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)]),
        (date(2026, 1, 11), [date(2026, 1, 9), date(2026, 1, 10), date(2026, 1, 11)]),
        (date(2026, 1, 15), [date(2026, 1, 13), date(2026, 1, 14), date(2026, 1, 15)]),
    ]


def test_historical_generation_rejects_unsorted_price_sequences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InspectingStrategy:
        def lookback_days(self) -> int:
            return 0

        def generate_signal(self, **kwargs):
            return []

    monkeypatch.setattr(generation, "resolve_strategy", lambda config: InspectingStrategy())
    with pytest.raises(ValueError, match="ascending"):
        generation.generate_historical_strategy_signals(
            historical_trading_dates=[date(2026, 1, 1)],
            config=_equal_config(),
            price_panel={
                1: [_price(1, date(2026, 1, 2)), _price(1, date(2026, 1, 1))],
            },
            active_etfs=[_etf(1, "A")],
        )


def test_historical_generation_long_history_never_exceeds_declared_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start = date(2026, 1, 1)
    trading_dates = [start.fromordinal(start.toordinal() + offset) for offset in range(366)]
    supplied_rows = 0

    class InspectingStrategy:
        def lookback_days(self) -> int:
            return 5

        def generate_signal(self, *, price_panel, **kwargs):
            nonlocal supplied_rows
            supplied_rows += sum(len(prices) for prices in price_panel.values())
            return []

    monkeypatch.setattr(generation, "resolve_strategy", lambda config: InspectingStrategy())
    results = generation.generate_historical_strategy_signals(
        historical_trading_dates=trading_dates,
        config=_equal_config(),
        price_panel={
            1: [_price(1, trade_date) for trade_date in trading_dates],
            2: [_price(2, trade_date) for trade_date in trading_dates],
        },
        active_etfs=[_etf(1, "A"), _etf(2, "B")],
    )

    assert supplied_rows <= len(results) * 2 * 6


def test_dual_momentum_reuses_prepared_series_for_trend_and_momentum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prices = [_price(1, date(2026, 1, 1)), _price(1, date(2026, 1, 2))]
    seen_series: list[list[MarketPrice]] = []

    def _trend(series, *, etf_id, as_of_date, parameters):
        seen_series.append(series)
        return TrendFilterResult(etf_id, as_of_date, Decimal("1"), Decimal("1"), True)

    def _momentum(series, *, etf_id, as_of_date, parameters):
        seen_series.append(series)
        return MomentumScore(etf_id, as_of_date, Decimal("0"), Decimal("0"), Decimal("0"))

    monkeypatch.setattr(dual_momentum, "_trend_filter_from_prices", _trend)
    monkeypatch.setattr(dual_momentum, "_momentum_score_from_prices", _momentum)
    DualMomentumStrategy(_dual_config().parameters).generate_signal(
        signal_date=date(2026, 1, 2), price_panel={1: prices}, active_etfs=[_etf(1, "A")]
    )

    assert seen_series[0] is seen_series[1]


def test_historical_generation_excludes_pre_inception_etfs_and_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_date = date(2026, 1, 1)
    second_date = date(2026, 1, 8)
    observed: list[tuple[list[int], dict[int, list[date]]]] = []

    class InspectingStrategy:
        def lookback_days(self) -> int:
            return 0

        def generate_signal(self, *, signal_date, price_panel, active_etfs):
            observed.append(
                (
                    [etf.id for etf in active_etfs],
                    {
                        etf_id: [price.trade_date for price in prices]
                        for etf_id, prices in price_panel.items()
                    },
                )
            )
            return []

    late = _etf(2, "LATE")
    late.listing_date = second_date
    monkeypatch.setattr(generation, "resolve_strategy", lambda config: InspectingStrategy())
    generation.generate_historical_strategy_signals(
        historical_trading_dates=[first_date, second_date],
        config=_equal_config(),
        price_panel={
            1: [_price(1, first_date), _price(1, second_date)],
            2: [_price(2, first_date), _price(2, second_date)],
        },
        active_etfs=[_etf(1, "EARLY"), late],
    )

    assert observed == [
        ([1], {1: [first_date]}),
        ([1, 2], {1: [second_date], 2: [second_date]}),
    ]


def test_generation_converts_expected_error_once_and_propagates_programming_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExpectedFailure:
        def generate_signal(self, **kwargs):
            raise StrategyGenerationError("expected")

        def lookback_days(self) -> int:
            return 0

    calls: list[str] = []
    monkeypatch.setattr(generation, "resolve_strategy", lambda config: ExpectedFailure())
    result = generation.generate_strategy_signal(
        signal_date=date(2026, 1, 1),
        config=_equal_config(),
        price_panel={},
        active_etfs=[_etf(1, "A")],
        persist=lambda **kwargs: calls.append(kwargs["status"]) or 9,
    )

    assert (result.status, result.error_message, result.strategy_signal_id, calls) == (
        "failed",
        "expected",
        9,
        ["failed"],
    )

    class Bug:
        def generate_signal(self, **kwargs):
            raise RuntimeError("bug")

        def lookback_days(self) -> int:
            return 0

    monkeypatch.setattr(generation, "resolve_strategy", lambda config: Bug())
    with pytest.raises(RuntimeError, match="bug"):
        generation.generate_strategy_signal(
            signal_date=date(2026, 1, 1),
            config=_equal_config(),
            price_panel={},
            active_etfs=[_etf(1, "A")],
        )


def _equal_config():
    return validate_strategy_config(
        {
            "strategy_id": "equal_weight",
            "version": "v1",
            "type": "equal_weight",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {},
            "costs": {"transaction_cost_bps": 0},
            "performance": {"risk_free_rate": 0},
        }
    )


def _dual_config():
    return validate_strategy_config(
        {
            "strategy_id": "dual_momentum",
            "version": "v1",
            "type": "dual_momentum",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {
                "momentum": {"short_window_days": 63, "long_window_days": 126},
                "score_weights": {"short": 0.4, "long": 0.6},
                "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                "selection": {"top_n": 1},
                "defense": {"assets": [{"exchange": "X", "symbol": "D"}]},
            },
            "costs": {"transaction_cost_bps": 0},
            "performance": {"risk_free_rate": 0},
        }
    )


def _etf(etf_id: int, symbol: str) -> ETFInfo:
    return ETFInfo(
        id=etf_id,
        exchange="X",
        symbol=symbol,
        name=symbol,
        currency="CNY",
        listing_date=date(1900, 1, 1),
    )


def _price(etf_id: int, trade_date: date) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=Decimal("1"),
        high_price=Decimal("1"),
        low_price=Decimal("1"),
        close_price=Decimal("1"),
        factor_hfq=Decimal("1"),
        volume=1,
    )
