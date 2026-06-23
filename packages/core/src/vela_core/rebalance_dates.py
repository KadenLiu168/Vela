from collections.abc import Iterable
from datetime import date


def generate_weekly_rebalance_dates(trading_dates: Iterable[date]) -> list[date]:
    weekly_rebalance_dates: dict[tuple[int, int], date] = {}

    for trading_date in sorted(set(trading_dates)):
        iso_year, iso_week, _ = trading_date.isocalendar()
        weekly_rebalance_dates[(iso_year, iso_week)] = trading_date

    return sorted(weekly_rebalance_dates.values())
