"""Trading calendar sync from akshare into the local database.

This module provides the sync workflow that fetches A-share trading days
from akshare ``tool_trade_date_hist_sina`` and upserts them into the
``trading_calendar`` table. It is a pure data-infrastructure primitive:
it does not perform any gap detection (that lives in a separate change)
and does not write ``DataFetchLog`` rows (the calendar is low-frequency
metadata synced independently of market-price fetches).
"""

from dataclasses import dataclass
from datetime import date, datetime
from importlib import import_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from vela_core.models import TradingCalendar


@dataclass(frozen=True)
class TradingCalendarSyncResult:
    synced_count: int
    inserted_count: int
    updated_count: int
    status: str
    error_message: str | None = None


def sync_trading_calendar_to_db(
    session: Session,
    *,
    source: str = "akshare",
) -> TradingCalendarSyncResult:
    """Fetch A-share trading days from akshare and upsert them into ``trading_calendar``.

    On akshare failure (import error, call error, or parse error) the function
    returns a ``failed`` result with an error message rather than raising, so
    CLI callers can report the failure without a traceback.
    """
    try:
        akshare = import_module("akshare")
        df = akshare.tool_trade_date_hist_sina()
        trade_dates = _parse_trade_dates(df)
    except Exception as exc:
        return TradingCalendarSyncResult(
            synced_count=0,
            inserted_count=0,
            updated_count=0,
            status="failed",
            error_message=f"akshare trading calendar fetch failed: {exc}",
        )

    if not trade_dates:
        return TradingCalendarSyncResult(
            synced_count=0,
            inserted_count=0,
            updated_count=0,
            status="failed",
            error_message="akshare returned no trade dates",
        )

    existing = set(
        session.scalars(
            select(TradingCalendar.trade_date).where(TradingCalendar.trade_date.in_(trade_dates))
        )
    )
    rows = [{"trade_date": trade_date, "source": source} for trade_date in trade_dates]
    statement = insert(TradingCalendar).on_conflict_do_update(
        index_elements=[TradingCalendar.trade_date],
        set_={
            "source": insert(TradingCalendar).excluded.source,
            "updated_at": func.now(),
        },
    )
    session.execute(statement, rows)
    session.flush()

    inserted_count = len(trade_dates) - len(existing)
    updated_count = len(existing)
    return TradingCalendarSyncResult(
        synced_count=len(trade_dates),
        inserted_count=inserted_count,
        updated_count=updated_count,
        status="success",
        error_message=None,
    )


def _parse_trade_dates(df: Any) -> list[date]:
    """Extract sorted unique trading dates from the akshare DataFrame.

    akshare ``tool_trade_date_hist_sina`` returns a DataFrame with a
    ``trade_date`` column whose cells may be ``datetime``, ``date``, or
    ISO-date strings depending on the pandas/akshare version.
    """
    dates: list[date] = []
    for value in df["trade_date"]:
        if isinstance(value, datetime):
            dates.append(value.date())
        elif isinstance(value, date):
            dates.append(value)
        else:
            dates.append(date.fromisoformat(str(value)))
    return sorted(set(dates))
