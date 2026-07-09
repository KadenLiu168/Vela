"""Market data quality detection helpers.

This module provides pure, session-free functions that inspect a batch of
fetched market prices for data-quality problems (currently duplicate trade
dates) and serialize the findings into a JSON envelope stored on
``DataFetchLog.quality_warnings``.

The detectors are deliberately decoupled from the fetch/upsert pipeline:
they accept in-memory sequences and return structured warnings, so they can
be unit-tested without a database and extended by future quality checks
without touching the ingestion layer.
"""

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from vela_core.models import MarketPrice


@dataclass(frozen=True)
class DuplicateTradeDateWarning:
    """A single ``(etf_id, trade_date)`` key collapsed more than once in a fetch batch."""

    etf_id: int
    trade_date: date
    count: int


def detect_duplicate_trade_dates(
    prices: Sequence[MarketPrice],
) -> list[DuplicateTradeDateWarning]:
    """Return one warning per ``(etf_id, trade_date)`` key that appears more than once.

    Pure function: does not hold a database session and does not mutate
    ``prices``. Results are sorted by ``(etf_id, trade_date)`` for deterministic
    output.
    """
    counts: Counter[tuple[int, date]] = Counter()
    for price in prices:
        counts[(price.etf_id, price.trade_date)] += 1

    warnings = [
        DuplicateTradeDateWarning(etf_id=etf_id, trade_date=trade_date, count=count)
        for (etf_id, trade_date), count in counts.items()
        if count > 1
    ]
    warnings.sort(key=lambda warning: (warning.etf_id, warning.trade_date))
    return warnings


def build_quality_warnings_json(
    warnings: Sequence[DuplicateTradeDateWarning],
) -> str | None:
    """Serialize duplicate-trade-date warnings into the ``quality_warnings`` JSON envelope.

    Returns ``None`` when there are no warnings so the persisted
    ``DataFetchLog.quality_warnings`` column stays null for clean batches.
    The envelope uses a top-level ``duplicate_trade_dates`` key so future
    detectors (e.g. trading-day gaps) can add sibling keys without breaking
    existing consumers.
    """
    if not warnings:
        return None

    return json.dumps(
        {
            "duplicate_trade_dates": [
                {
                    "etf_id": warning.etf_id,
                    "trade_date": warning.trade_date.isoformat(),
                    "count": warning.count,
                }
                for warning in warnings
            ]
        },
        sort_keys=True,
    )


@dataclass(frozen=True)
class SystematicTradingDayGap:
    """A trading day the calendar says should exist but that no ETF has stored data for."""

    trade_date: date


@dataclass(frozen=True)
class EtfTradingDayGap:
    """A trading day missing for a specific ETF (the calendar says it should exist)."""

    etf_id: int
    trade_date: date


def detect_systematic_trading_day_gaps(
    actual_dates: Sequence[date],
    expected_dates: Sequence[date],
) -> list[SystematicTradingDayGap]:
    """Return one warning per calendar trading day absent from ``actual_dates``.

    Pure function: compares the union of stored trade dates against the
    trading-calendar days and flags every expected day that no ETF has data for.
    Dates present in ``actual_dates`` but absent from ``expected_dates`` are
    ignored (extra stored days are not gaps). Results are sorted ascending by
    ``trade_date`` for deterministic output.
    """
    expected_set = set(expected_dates)
    actual_set = set(actual_dates)
    missing = expected_set - actual_set
    return [SystematicTradingDayGap(trade_date=day) for day in sorted(missing)]


def detect_etf_trading_day_gaps(
    etf_actual_dates: Mapping[int, Sequence[date]],
    expected_dates: Sequence[date],
    inception_boundaries: Mapping[int, date],
) -> list[EtfTradingDayGap]:
    """Return one warning per ``(etf_id, trade_date)`` gap, suppressing pre-inception days.

    Pure function: for each ETF in ``etf_actual_dates``, compares its stored
    trade dates against the trading-calendar days that fall on or after the
    ETF's inception boundary (``max(inception_date, first_stored_date)``,
    supplied by the caller). Gaps before the boundary are suppressed so
    pre-listing and partial-first-record periods are not flagged. ETFs absent
    from ``etf_actual_dates`` (no stored rows) are skipped. ETFs without an
    entry in ``inception_boundaries`` default to ``date.min`` (no suppression).
    Results are sorted by ``(etf_id, trade_date)`` for deterministic output.
    """
    expected_set = set(expected_dates)
    warnings: list[EtfTradingDayGap] = []
    for etf_id, actual in etf_actual_dates.items():
        boundary = inception_boundaries.get(etf_id, date.min)
        actual_set = set(actual)
        for expected_day in expected_set:
            if expected_day < boundary:
                continue
            if expected_day not in actual_set:
                warnings.append(EtfTradingDayGap(etf_id=etf_id, trade_date=expected_day))
    warnings.sort(key=lambda warning: (warning.etf_id, warning.trade_date))
    return warnings


def build_quality_warnings_json_from_sections(
    duplicate_warnings: Sequence[DuplicateTradeDateWarning],
    systematic_gaps: Sequence[SystematicTradingDayGap],
    etf_gaps: Sequence[EtfTradingDayGap],
) -> str | None:
    """Serialize duplicate and gap warnings into a single ``quality_warnings`` JSON envelope.

    Returns ``None`` when all sections are empty so the persisted
    ``DataFetchLog.quality_warnings`` column stays null for clean batches. The
    envelope uses top-level keys ``duplicate_trade_dates``,
    ``systematic_trading_day_gaps``, and ``etf_trading_day_gaps``; empty sections
    are omitted. The ``duplicate_trade_dates`` section serializes identically to
    :func:`build_quality_warnings_json` so existing consumers are not broken.
    """
    envelope: dict[str, list[dict[str, object]]] = {}
    if duplicate_warnings:
        envelope["duplicate_trade_dates"] = [
            {
                "etf_id": warning.etf_id,
                "trade_date": warning.trade_date.isoformat(),
                "count": warning.count,
            }
            for warning in duplicate_warnings
        ]
    if systematic_gaps:
        envelope["systematic_trading_day_gaps"] = [
            {"trade_date": gap.trade_date.isoformat()} for gap in systematic_gaps
        ]
    if etf_gaps:
        envelope["etf_trading_day_gaps"] = [
            {"etf_id": gap.etf_id, "trade_date": gap.trade_date.isoformat()} for gap in etf_gaps
        ]
    if not envelope:
        return None
    return json.dumps(envelope, sort_keys=True)
