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
from collections.abc import Sequence
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
