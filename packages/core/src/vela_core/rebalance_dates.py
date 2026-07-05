from collections.abc import Iterable
from datetime import date
from typing import Literal

RebalanceFrequency = Literal["weekly", "monthly"]


def generate_weekly_rebalance_dates(trading_dates: Iterable[date]) -> list[date]:
    weekly_rebalance_dates: dict[tuple[int, int], date] = {}

    for trading_date in sorted(set(trading_dates)):
        iso_year, iso_week, _ = trading_date.isocalendar()
        weekly_rebalance_dates[(iso_year, iso_week)] = trading_date

    return sorted(weekly_rebalance_dates.values())


def generate_monthly_rebalance_dates(trading_dates: Iterable[date]) -> list[date]:
    monthly_rebalance_dates: dict[tuple[int, int], date] = {}

    for trading_date in sorted(set(trading_dates)):
        monthly_rebalance_dates[(trading_date.year, trading_date.month)] = trading_date

    return sorted(monthly_rebalance_dates.values())


def generate_rebalance_dates(
    trading_dates: Iterable[date],
    *,
    frequency: RebalanceFrequency,
) -> list[date]:
    if frequency == "weekly":
        return generate_weekly_rebalance_dates(trading_dates)
    if frequency == "monthly":
        return generate_monthly_rebalance_dates(trading_dates)
    raise ValueError(f"Unsupported rebalance frequency: {frequency!r}")
