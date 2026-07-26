from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: date
    train_end: date
    test_start: date
    test_end: date


def _shift_years(value: date, years: int) -> date:
    target_year = value.year + years
    return value.replace(
        year=target_year, day=min(value.day, monthrange(target_year, value.month)[1])
    )


def _bounds(dates: list[date], start: date, end_exclusive: date) -> tuple[date, date]:
    interval = [item for item in dates if start <= item < end_exclusive]
    if not interval:
        raise ValueError(
            f"complete calendar interval {start} to {end_exclusive} has no trading dates"
        )
    return interval[0], interval[-1]


def generate_windows(
    trading_dates: list[date],
    start_date: date,
    end_date: date,
    train_years: int,
    test_years: int,
    step_years: int,
) -> list[WalkForwardWindow]:
    if min(train_years, test_years, step_years) <= 0:
        raise ValueError("window lengths must be positive")
    end_exclusive = end_date + timedelta(days=1)
    dates = sorted(set(item for item in trading_dates if start_date <= item <= end_date))
    first_complete_end = _shift_years(start_date, train_years + test_years)
    if first_complete_end > end_exclusive:
        raise ValueError("insufficient configured range for one complete window")
    windows: list[WalkForwardWindow] = []
    index = 0
    anchor = start_date
    while _shift_years(anchor, train_years + test_years) <= end_exclusive:
        train_end_exclusive = _shift_years(anchor, train_years)
        test_end_exclusive = _shift_years(anchor, train_years + test_years)
        train_start, train_end = _bounds(dates, anchor, train_end_exclusive)
        test_start, test_end = _bounds(dates, train_end_exclusive, test_end_exclusive)
        windows.append(WalkForwardWindow(train_start, train_end, test_start, test_end))
        index += 1
        anchor = _shift_years(start_date, index * step_years)
    return windows
