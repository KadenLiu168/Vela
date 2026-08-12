from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.backtest_input import build_backtest_input_v2
from vela_core.models import ETFInfo, TradingCalendar
from vela_core.resolved_session_price import ResolvedSessionPrice
from vela_core.resolved_session_price_query import load_resolved_session_price_panel
from vela_core.strategies.registry import resolve_strategy
from vela_core.strategy_config import StrategyConfig
from vela_core.walk_forward.config import WalkForwardConfig
from vela_core.walk_forward.parameter_space import (
    build_strategy_config,
    generate_combinations,
)
from vela_core.walk_forward.provenance import (
    PROVENANCE_VERSION_V2,
    STATUS_EVIDENCE_SAMPLE_LIMIT,
    input_record_stream,
    sha256_hex,
)
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
    _validate_listing_metadata(active_etfs)
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
    resolved_panel = load_resolved_session_price_panel(
        session,
        active_etfs=active_etfs,
        official_sessions=official_sessions,
    )
    following_session = session.scalar(
        select(TradingCalendar.trade_date)
        .where(TradingCalendar.trade_date > window_config.end_date)
        .order_by(TradingCalendar.trade_date)
        .limit(1)
    )
    manifest, records = _build_manifest(
        active_etfs=active_etfs,
        price_panel=resolved_panel,
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


def _validate_listing_metadata(active_etfs: list[ETFInfo]) -> None:
    missing = [f"{etf.exchange}:{etf.symbol}" for etf in active_etfs if etf.listing_date is None]
    if missing:
        raise ValueError("missing listing_date for active ETF " + ", ".join(missing))


def _build_manifest(
    *,
    active_etfs: list[ETFInfo],
    price_panel: Mapping[int, Sequence[ResolvedSessionPrice]],
    official_sessions: list[date],
    earliest_required_session: date,
    configured_end_date: date,
    following_session: date | None,
) -> tuple[dict[str, object], list[list[Any]]]:
    snapshot = build_backtest_input_v2(
        active_etfs=active_etfs,
        official_sessions=official_sessions,
        following_session=following_session,
        price_panel=price_panel,
    )
    raw_records = snapshot["raw_price_records"]
    derived_records = snapshot["derived_sessions"]
    assert isinstance(raw_records, list)
    assert isinstance(derived_records, list)
    active_etf_manifest: list[dict[str, object]] = []
    etf_records: list[list[Any]] = []
    for etf in active_etfs:
        raw = [item for item in raw_records if item["etf_id"] == etf.id]
        derived = [item for item in derived_records if item["etf_id"] == etf.id]
        active_etf_manifest.append(
            {
                "etf_id": etf.id,
                "exchange": etf.exchange,
                "symbol": etf.symbol,
                "inception_date": _iso(etf.inception_date),
                "listing_date": _iso(etf.listing_date),
                "raw_price_row_count": len(raw),
                "first_raw_price_date": _first_date(raw),
                "last_raw_price_date": _last_date(raw),
                "derived_session_count": len(derived),
                "first_derived_session_date": _first_date(derived),
                "last_derived_session_date": _last_date(derived),
                "status_evidence": [
                    {
                        key: item[key]
                        for key in (
                            "trade_date",
                            "status",
                            "reason",
                            "source_uri",
                            "source_published_date",
                            "share_ratio",
                            "resolution",
                            "carried_adjusted_value",
                            "carry_from_trade_date",
                        )
                    }
                    for item in derived[:STATUS_EVIDENCE_SAMPLE_LIMIT]
                ],
            }
        )
        etf_records.append(
            [
                "etf",
                etf.id,
                etf.exchange,
                etf.symbol,
                _iso(etf.inception_date),
                _iso(etf.listing_date),
            ]
        )
    records: list[list[Any]] = [
        ["version", PROVENANCE_VERSION_V2],
        ["policy", snapshot["resolution_policy_version"]],
        *etf_records,
    ]
    records.extend(["session", item] for item in (_iso(value) for value in official_sessions))
    records.append(["following_session", _iso(following_session)])
    records.extend(
        [
            "raw",
            item["etf_id"],
            item["exchange"],
            item["symbol"],
            item["trade_date"],
            item["close_price"],
            item["factor_hfq"],
        ]
        for item in raw_records
    )
    records.extend(
        [
            "derived",
            item["etf_id"],
            item["exchange"],
            item["symbol"],
            item["trade_date"],
            item["status"],
            item["reason"],
            item["source_uri"],
            item["source_published_date"],
            item["share_ratio"],
            item["resolution"],
            item["carried_adjusted_value"],
            item["carry_from_trade_date"],
        ]
        for item in derived_records
    )
    manifest: dict[str, object] = {
        "version": PROVENANCE_VERSION_V2,
        "resolution_policy_version": snapshot["resolution_policy_version"],
        "earliest_required_session": earliest_required_session.isoformat(),
        "configured_end_date": configured_end_date.isoformat(),
        "following_session": _iso(following_session),
        "official_sessions": [value.isoformat() for value in official_sessions],
        "active_etfs": active_etf_manifest,
        "raw_price_row_count": len(raw_records),
        "first_raw_price_date": _first_date(raw_records),
        "last_raw_price_date": _last_date(raw_records),
        "derived_session_count": len(derived_records),
        "first_derived_session_date": _first_date(derived_records),
        "last_derived_session_date": _last_date(derived_records),
    }
    return manifest, records


def _iso(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _first_date(records: list[dict[str, object]]) -> str | None:
    return min((str(item["trade_date"]) for item in records), default=None)


def _last_date(records: list[dict[str, object]]) -> str | None:
    return max((str(item["trade_date"]) for item in records), default=None)
