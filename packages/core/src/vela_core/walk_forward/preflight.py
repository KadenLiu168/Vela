from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, MarketPrice, TradingCalendar
from vela_core.strategies.registry import resolve_strategy
from vela_core.strategy_config import StrategyConfig
from vela_core.walk_forward.config import WalkForwardConfig
from vela_core.walk_forward.parameter_space import (
    build_strategy_config,
    generate_combinations,
)
from vela_core.walk_forward.provenance import PROVENANCE_VERSION, input_record_stream, sha256_hex
from vela_core.walk_forward.window_splitter import WalkForwardWindow, generate_windows


@dataclass(frozen=True)
class WalkForwardPreflight:
    windows: list[WalkForwardWindow]
    manifest: dict[str, object]
    input_data_checksum: str
    maximum_lookback_days: int
    valid_candidates: tuple[StrategyConfig, ...]


def prepare_walk_forward_inputs(
    session: Session, *, config: WalkForwardConfig, base_config: dict[str, Any] | None = None
) -> WalkForwardPreflight:
    base_config = (
        base_config if base_config is not None else _load_base_config(config.strategy.base_config)
    )
    combinations = generate_combinations(config.parameter_space)
    valid_candidates: list[StrategyConfig] = []
    maximum_lookback_days = 0
    for combination in combinations:
        built = build_strategy_config(base_config, combination)
        if built.config is None:
            continue
        lookback_days = resolve_strategy(built.config).lookback_days()
        if lookback_days < 0:
            raise ValueError("Strategy lookback_days must be non-negative")
        valid_candidates.append(built.config)
        maximum_lookback_days = max(maximum_lookback_days, lookback_days)
    if not valid_candidates:
        raise ValueError("no valid parameter combinations before source OOS evaluation")

    window_config = config.window
    configured_sessions = list(
        session.scalars(
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date >= window_config.start_date)
            .where(TradingCalendar.trade_date <= window_config.end_date)
            .order_by(TradingCalendar.trade_date)
        )
    )
    if not configured_sessions:
        raise ValueError("official trading calendar has no sessions in configured range")
    active_etfs = list(
        session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.id))
    )
    preceding = list(
        session.scalars(
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date < configured_sessions[0])
            .order_by(TradingCalendar.trade_date.desc())
            .limit(maximum_lookback_days)
        )
    )
    if active_etfs and len(preceding) != maximum_lookback_days:
        raise ValueError("official trading calendar lacks the required lookback envelope")
    official_sessions = sorted({*preceding, *configured_sessions})
    windows = generate_windows(
        official_sessions,
        window_config.start_date,
        window_config.end_date,
        window_config.train_years,
        window_config.test_years,
        window_config.step_years,
    )
    earliest_required_session = official_sessions[0]
    price_panel = load_price_panel(
        session,
        etf_ids=[etf.id for etf in active_etfs],
        start_date=earliest_required_session,
        end_date=window_config.end_date,
    )
    _validate_required_prices(active_etfs, official_sessions, price_panel)
    following_session = session.scalar(
        select(TradingCalendar.trade_date)
        .where(TradingCalendar.trade_date > window_config.end_date)
        .order_by(TradingCalendar.trade_date)
        .limit(1)
    )
    manifest, records = _build_manifest(
        active_etfs=active_etfs,
        price_panel=price_panel,
        official_sessions=official_sessions,
        earliest_required_session=earliest_required_session,
        configured_end_date=window_config.end_date,
        following_session=following_session,
    )
    return WalkForwardPreflight(
        windows=windows,
        manifest=manifest,
        input_data_checksum=sha256_hex(input_record_stream(records)),
        maximum_lookback_days=maximum_lookback_days,
        valid_candidates=tuple(valid_candidates),
    )


def _load_base_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"base strategy configuration {path} must be a mapping")
    return data


def _validate_required_prices(
    active_etfs: list[ETFInfo],
    official_sessions: list[date],
    price_panel: dict[int, list[MarketPrice]],
) -> None:
    available = {
        (price.etf_id, price.trade_date) for prices in price_panel.values() for price in prices
    }
    missing = [
        (etf.id, trade_date)
        for etf in active_etfs
        for trade_date in official_sessions
        if (etf.inception_date is None or trade_date >= etf.inception_date)
        and (etf.id, trade_date) not in available
    ]
    if missing:
        raise ValueError(f"missing required market price for ETF/session {missing[0]}")


def _build_manifest(
    *,
    active_etfs: list[ETFInfo],
    price_panel: dict[int, list[MarketPrice]],
    official_sessions: list[date],
    earliest_required_session: date,
    configured_end_date: date,
    following_session: date | None,
) -> tuple[dict[str, object], list[list[Any]]]:
    etf_records: list[list[Any]] = []
    active_etf_manifest: list[dict[str, object]] = []
    loaded_rows: list[MarketPrice] = []
    for etf in active_etfs:
        rows = [
            row
            for row in price_panel.get(etf.id, [])
            if (etf.inception_date is None or row.trade_date >= etf.inception_date)
            and row.trade_date <= configured_end_date
        ]
        loaded_rows.extend(rows)
        active_etf_manifest.append(
            {
                "etf_id": etf.id,
                "exchange": etf.exchange,
                "symbol": etf.symbol,
                "inception_date": _iso(etf.inception_date),
                "loaded_price_row_count": len(rows),
                "first_loaded_price_date": _iso(
                    min((row.trade_date for row in rows), default=None)
                ),
                "last_loaded_price_date": _iso(max((row.trade_date for row in rows), default=None)),
            }
        )
        etf_records.append(["etf", etf.id, etf.exchange, etf.symbol, _iso(etf.inception_date)])
    loaded_rows.sort(key=lambda row: (row.etf_id, row.trade_date))
    records: list[list[Any]] = [["version", PROVENANCE_VERSION], *etf_records]
    records.extend(["session", item] for item in (_iso(value) for value in official_sessions))
    records.append(["following_session", _iso(following_session)])
    records.extend(
        [
            "price",
            row.etf_id,
            next(etf.exchange for etf in active_etfs if etf.id == row.etf_id),
            next(etf.symbol for etf in active_etfs if etf.id == row.etf_id),
            row.trade_date.isoformat(),
            str(row.close_price),
            str(row.factor_hfq),
        ]
        for row in loaded_rows
    )
    manifest: dict[str, object] = {
        "version": PROVENANCE_VERSION,
        "earliest_required_session": earliest_required_session.isoformat(),
        "configured_end_date": configured_end_date.isoformat(),
        "following_session": _iso(following_session),
        "official_sessions": [value.isoformat() for value in official_sessions],
        "active_etfs": active_etf_manifest,
        "loaded_price_row_count": len(loaded_rows),
        "first_loaded_price_date": _iso(min((row.trade_date for row in loaded_rows), default=None)),
        "last_loaded_price_date": _iso(max((row.trade_date for row in loaded_rows), default=None)),
    }
    return manifest, records


def _iso(value: date | None) -> str | None:
    return None if value is None else value.isoformat()
