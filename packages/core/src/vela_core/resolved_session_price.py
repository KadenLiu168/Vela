from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal, cast

from vela_core.models import ETFInfo, ETFSessionStatus, MarketPrice

RESOLUTION_POLICY_VERSION = "resolved_session_price_v1"
ResolvedSessionResolution = Literal["market_price", "confirmed_non_trading_carry"]
_SUPPORTED_STATUSES = {"full_day_suspension", "corporate_action_halt"}
_FAILURE_CATEGORIES = (
    "missing_listing_metadata",
    "unexplained_gap",
    "raw_status_conflict",
    "missing_carry_anchor",
)


@dataclass(frozen=True)
class ResolvedSessionPrice:
    etf_id: int
    trade_date: date
    adjusted_value: Decimal
    raw_close: Decimal | None
    raw_factor: Decimal | None
    tradable: bool
    resolution: ResolvedSessionResolution
    status: str | None = None
    reason: str | None = None
    source_uri: str | None = None
    source_published_date: date | None = None
    share_ratio: Decimal | None = None
    carry_from_trade_date: date | None = None


@dataclass(frozen=True)
class ResolutionFailure:
    category: str
    etf_id: int
    exchange: str
    symbol: str
    trade_date: date | None

    def sort_key(self) -> tuple[str, int, date]:
        return (self.category, self.etf_id, self.trade_date or date.min)

    def format(self) -> str:
        identity = f"ETF {self.etf_id} {self.exchange}:{self.symbol}"
        if self.trade_date is None:
            return f"{self.category}: {identity} listing_date=missing"
        return f"{self.category}: {identity} on {self.trade_date.isoformat()}"


class ResolvedSessionInputError(ValueError):
    def __init__(self, failures: Sequence[ResolutionFailure], *, sample_limit: int = 10) -> None:
        ordered = tuple(sorted(failures, key=ResolutionFailure.sort_key))
        counts = Counter(failure.category for failure in ordered)
        self.failures = ordered
        self.category_counts = {
            category: counts[category] for category in _FAILURE_CATEGORIES if counts[category]
        }
        self.samples = tuple(failure.format() for failure in ordered[:sample_limit])
        count_text = ", ".join(
            f"{category}={count}" for category, count in self.category_counts.items()
        )
        sample_text = "; ".join(self.samples)
        message = f"Resolved session input validation failed: {count_text}"
        if sample_text:
            message += f"; sample: {sample_text}"
        super().__init__(message)


def resolve_session_prices(
    *,
    official_sessions: Sequence[date],
    active_etfs: Sequence[ETFInfo],
    raw_prices: Mapping[int, Sequence[MarketPrice]] | Sequence[MarketPrice],
    session_statuses: Mapping[int, Sequence[ETFSessionStatus]] | Sequence[ETFSessionStatus],
    sample_limit: int = 10,
) -> dict[int, list[ResolvedSessionPrice]]:
    sessions = list(official_sessions)
    if any(previous >= current for previous, current in zip(sessions, sessions[1:], strict=False)):
        raise ValueError("official_sessions must be strictly ascending")
    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")

    etfs = sorted(active_etfs, key=lambda etf: etf.id or 0)
    if any(etf.id is None for etf in etfs):
        raise ValueError("active ETF ids are required for session resolution")
    if len({etf.id for etf in etfs}) != len(etfs):
        raise ValueError("active ETF ids must be unique for session resolution")

    prices_by_etf = _group_by_etf_id(raw_prices)
    statuses_by_etf = _group_by_etf_id(session_statuses)
    failures: list[ResolutionFailure] = []
    resolved: dict[int, list[ResolvedSessionPrice]] = {}

    for etf in etfs:
        assert etf.id is not None
        if etf.listing_date is None:
            failures.append(
                ResolutionFailure(
                    category="missing_listing_metadata",
                    etf_id=etf.id,
                    exchange=etf.exchange,
                    symbol=etf.symbol,
                    trade_date=None,
                )
            )
            continue

        raw_by_date = _rows_by_date(prices_by_etf.get(etf.id, ()))
        status_by_date = _rows_by_date(statuses_by_etf.get(etf.id, ()))
        etf_resolved: list[ResolvedSessionPrice] = []
        last_resolved: ResolvedSessionPrice | None = None

        for trade_date in sessions:
            if trade_date < etf.listing_date:
                continue

            raw_rows = raw_by_date.get(trade_date, [])
            status_rows = status_by_date.get(trade_date, [])
            if len(raw_rows) != 1 or len(status_rows) != 1 and status_rows:
                if len(raw_rows) > 1 or len(status_rows) > 1:
                    failures.append(
                        _failure(
                            "raw_status_conflict",
                            etf,
                            trade_date,
                        )
                    )
                    continue
            if raw_rows and status_rows:
                failures.append(_failure("raw_status_conflict", etf, trade_date))
                continue

            if raw_rows:
                raw = cast(MarketPrice, raw_rows[0])
                point = ResolvedSessionPrice(
                    etf_id=etf.id,
                    trade_date=trade_date,
                    adjusted_value=raw.close_price * raw.factor_hfq,
                    raw_close=raw.close_price,
                    raw_factor=raw.factor_hfq,
                    tradable=True,
                    resolution="market_price",
                )
                etf_resolved.append(point)
                last_resolved = point
                continue

            if status_rows:
                status = cast(ETFSessionStatus, status_rows[0])
                _validate_status(status, etf, trade_date)
                if last_resolved is None:
                    failures.append(_failure("missing_carry_anchor", etf, trade_date))
                    continue
                point = ResolvedSessionPrice(
                    etf_id=etf.id,
                    trade_date=trade_date,
                    adjusted_value=last_resolved.adjusted_value,
                    raw_close=None,
                    raw_factor=None,
                    tradable=False,
                    resolution="confirmed_non_trading_carry",
                    status=status.status,
                    reason=status.reason,
                    source_uri=status.source_uri,
                    source_published_date=status.source_published_date,
                    share_ratio=status.share_ratio,
                    carry_from_trade_date=last_resolved.trade_date,
                )
                etf_resolved.append(point)
                last_resolved = point
                continue

            failures.append(_failure("unexplained_gap", etf, trade_date))

        resolved[etf.id] = etf_resolved

    if failures:
        raise ResolvedSessionInputError(failures, sample_limit=sample_limit)
    return resolved


def _group_by_etf_id(
    rows: (
        Mapping[int, Sequence[MarketPrice]]
        | Mapping[int, Sequence[ETFSessionStatus]]
        | Sequence[object]
    ),
) -> dict[int, list[object]]:
    if isinstance(rows, Mapping):
        return {int(etf_id): list(values) for etf_id, values in rows.items()}

    grouped: dict[int, list[object]] = defaultdict(list)
    for row in rows:
        etf_id = getattr(row, "etf_id", None)
        if etf_id is None:
            raise ValueError("session input rows require etf_id")
        grouped[etf_id].append(row)
    return dict(grouped)


def _rows_by_date(rows: Sequence[object]) -> dict[date, list[object]]:
    grouped: dict[date, list[object]] = defaultdict(list)
    for row in rows:
        trade_date = getattr(row, "trade_date", None)
        if not isinstance(trade_date, date):
            raise ValueError("session input rows require trade_date")
        grouped[trade_date].append(row)
    return dict(grouped)


def _failure(category: str, etf: ETFInfo, trade_date: date) -> ResolutionFailure:
    assert etf.id is not None
    return ResolutionFailure(
        category=category,
        etf_id=etf.id,
        exchange=etf.exchange,
        symbol=etf.symbol,
        trade_date=trade_date,
    )


def _validate_status(status: object, etf: ETFInfo, trade_date: date) -> None:
    status_name = getattr(status, "status", None)
    if status_name not in _SUPPORTED_STATUSES:
        raise ValueError(
            f"Unsupported ETF session status for {etf.exchange}:{etf.symbol} "
            f"on {trade_date.isoformat()}: {status_name}"
        )
    for field_name in ("reason", "source_uri", "source_published_date"):
        if not getattr(status, field_name, None):
            raise ValueError(
                f"ETF session status {field_name} is required for "
                f"{etf.exchange}:{etf.symbol} on {trade_date.isoformat()}"
            )
    share_ratio = getattr(status, "share_ratio", None)
    if share_ratio is not None and share_ratio <= 0:
        raise ValueError(
            f"ETF session status share_ratio must be positive for "
            f"{etf.exchange}:{etf.symbol} on {trade_date.isoformat()}"
        )
