from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol, TypedDict

from vela_core.models import ETFInfo, MarketPrice
from vela_core.momentum_scoring import (
    DefensiveFallbackSelection,
    TopNSelection,
    _momentum_score_from_prices,
    rank_momentum_scores,
    select_with_defensive_fallback,
)
from vela_core.rebalance_dates import generate_rebalance_dates
from vela_core.strategy_config import StrategyConfig
from vela_core.trend_filter import _trend_filter_from_prices


@dataclass(frozen=True)
class GeneratedSignalPosition:
    etf_id: int
    exchange: str
    symbol: str
    target_weight: Decimal
    rank: int | None = None
    score: Decimal | None = None


@dataclass(frozen=True)
class GenerateStrategySignalResult:
    strategy_signal_id: int | None
    signal_date: date
    config_version: str
    status: str
    result: str | None
    error_message: str | None
    positions: list[GeneratedSignalPosition]


class PersistStrategySignalPosition(TypedDict):
    etf_id: int
    rank: int | None
    score: Decimal | None
    target_weight: Decimal


class PersistStrategySignalCallable(Protocol):
    def __call__(
        self,
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[PersistStrategySignalPosition],
        error_message: str | None,
    ) -> int: ...


def generate_strategy_signal(
    *,
    signal_date: date,
    config: StrategyConfig,
    price_panel: dict[int, list[MarketPrice]],
    active_etfs: list[ETFInfo],
    defense_lookup: dict[tuple[str, str], ETFInfo],
    generated_at: datetime | None = None,
    persist: PersistStrategySignalCallable | None = None,
) -> GenerateStrategySignalResult:
    """Generate a strategy signal for ``signal_date`` from injected inputs.

    Pure function: does not accept a database session and does not issue
    any ``MarketPrice`` queries. The caller must supply:

    - ``active_etfs``: the full active ETF universe (already loaded).
    - ``price_panel``: a ``{etf_id: ascending MarketPrice series}`` mapping
      covering at least the longest configured window through ``signal_date``.
    - ``defense_lookup``: ``{(exchange, symbol): ETFInfo}`` for resolving the
      defensive asset without a DB query.

    Persistence is delegated to the optional ``persist`` callback, which
    receives a positional payload describing the signal and returns the
    persisted ``strategy_signal.id`` (or ``None`` to skip persistence).
    """
    generated_at = generated_at or datetime.now(UTC)
    etfs_by_id = {etf.id: etf for etf in active_etfs}
    if not active_etfs:
        return _failed_result(
            signal_date=signal_date,
            config=config,
            error_message="No active ETFs found",
            generated_at=generated_at,
            persist=persist,
        )

    eligible_scores = [
        _momentum_score_from_prices(
            _prices_through(price_panel.get(etf.id, []), signal_date),
            etf_id=etf.id,
            as_of_date=signal_date,
            config=config,
        )
        for etf in active_etfs
        if _trend_filter_from_prices(
            _prices_through(price_panel.get(etf.id, []), signal_date),
            etf_id=etf.id,
            as_of_date=signal_date,
            config=config,
        ).passes_filter
    ]
    rankings = rank_momentum_scores(eligible_scores)
    selections = select_with_defensive_fallback(rankings, config)

    positions: list[GeneratedSignalPosition] = []
    for selection in selections:
        position = _to_generated_position(selection, etfs_by_id, defense_lookup)
        if position is None:
            # ``_to_generated_position`` returns ``None`` only when a defensive
            # fallback selection cannot be resolved via ``defense_lookup``;
            # narrow the union so the error message names the missing asset.
            if not isinstance(selection, DefensiveFallbackSelection):
                raise TypeError("None position is only expected for defensive fallback selections")
            return _failed_result(
                signal_date=signal_date,
                config=config,
                error_message=(
                    "Defensive asset not found as active ETF: "
                    f"{selection.exchange} {selection.symbol}"
                ),
                generated_at=generated_at,
                persist=persist,
            )
        positions.append(position)

    return _build_success_result(
        positions=positions,
        signal_date=signal_date,
        config=config,
        generated_at=generated_at,
        persist=persist,
    )


def generate_historical_strategy_signals(
    *,
    historical_trading_dates: Iterable[date],
    config: StrategyConfig,
    price_panel: dict[int, list[MarketPrice]],
    active_etfs: list[ETFInfo],
    defense_lookup: dict[tuple[str, str], ETFInfo],
    generated_at: datetime | None = None,
    persist: PersistStrategySignalCallable | None = None,
) -> list[GenerateStrategySignalResult]:
    """Generate signals for historical rebalance dates from an injected panel.

    Pure function: does not accept a database session and does not issue
    ``MarketPrice`` queries. The caller supplies the shared ``price_panel``
    covering the whole backtest window plus ``active_etfs`` and
    ``defense_lookup`` (typically built once for the whole backtest).
    """
    rebalance_dates = generate_rebalance_dates(
        historical_trading_dates,
        frequency=config.rebalance.frequency,
    )
    return [
        generate_strategy_signal(
            signal_date=rebalance_date,
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            defense_lookup=defense_lookup,
            generated_at=generated_at,
            persist=persist,
        )
        for rebalance_date in rebalance_dates
    ]


def _prices_through(
    prices: list[MarketPrice],
    signal_date: date,
) -> list[MarketPrice]:
    """Trim an ascending price series to rows on or before ``signal_date``.

    Assumes ``signal_date`` is the latest trading date in scope; this
    enforces the "no future data" guarantee from the historical
    signal-generation spec by truncation rather than by SQL.
    """
    return [price for price in prices if price.trade_date <= signal_date]


def _to_generated_position(
    selection: TopNSelection | DefensiveFallbackSelection,
    etfs_by_id: dict[int, ETFInfo],
    defense_lookup: dict[tuple[str, str], ETFInfo],
) -> GeneratedSignalPosition | None:
    if isinstance(selection, TopNSelection):
        etf = etfs_by_id[selection.etf_id]
        return GeneratedSignalPosition(
            etf_id=etf.id,
            exchange=etf.exchange,
            symbol=etf.symbol,
            rank=selection.rank,
            score=selection.score,
            target_weight=selection.target_weight,
        )

    defensive_etf = defense_lookup.get((selection.exchange, selection.symbol))
    if defensive_etf is None:
        return None

    return GeneratedSignalPosition(
        etf_id=defensive_etf.id,
        exchange=defensive_etf.exchange,
        symbol=defensive_etf.symbol,
        rank=selection.rank,
        score=selection.score,
        target_weight=selection.target_weight,
    )


def _build_success_result(
    *,
    positions: list[GeneratedSignalPosition],
    signal_date: date,
    config: StrategyConfig,
    generated_at: datetime,
    persist: PersistStrategySignalCallable | None,
) -> GenerateStrategySignalResult:
    payload_positions: list[PersistStrategySignalPosition] = [
        {
            "etf_id": position.etf_id,
            "rank": position.rank,
            "score": position.score,
            "target_weight": position.target_weight,
        }
        for position in positions
    ]
    result_label = "rebalance" if positions else "empty"

    if persist is None:
        return GenerateStrategySignalResult(
            strategy_signal_id=None,
            signal_date=signal_date,
            config_version=config.version,
            status="success",
            result=result_label,
            error_message=None,
            positions=positions,
        )

    signal_id = persist(
        signal_date=signal_date,
        generated_at=generated_at,
        status="success",
        result=result_label,
        positions=payload_positions,
        error_message=None,
    )
    return GenerateStrategySignalResult(
        strategy_signal_id=signal_id,
        signal_date=signal_date,
        config_version=config.version,
        status="success",
        result=result_label,
        error_message=None,
        positions=positions,
    )


def _failed_result(
    *,
    signal_date: date,
    config: StrategyConfig,
    error_message: str,
    generated_at: datetime,
    persist: PersistStrategySignalCallable | None,
) -> GenerateStrategySignalResult:
    if persist is None:
        return GenerateStrategySignalResult(
            strategy_signal_id=None,
            signal_date=signal_date,
            config_version=config.version,
            status="failed",
            result=None,
            error_message=error_message,
            positions=[],
        )

    signal_id = persist(
        signal_date=signal_date,
        generated_at=generated_at,
        status="failed",
        result=None,
        positions=[],
        error_message=error_message,
    )
    return GenerateStrategySignalResult(
        strategy_signal_id=signal_id,
        signal_date=signal_date,
        config_version=config.version,
        status="failed",
        result=None,
        error_message=error_message,
        positions=[],
    )
