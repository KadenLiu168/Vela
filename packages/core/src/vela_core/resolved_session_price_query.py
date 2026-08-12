from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, ETFSessionStatus, MarketPrice, TradingCalendar
from vela_core.resolved_session_price import ResolvedSessionPrice, resolve_session_prices


def load_resolved_session_price_panel(
    session: Session,
    *,
    active_etfs: Sequence[ETFInfo],
    official_sessions: Sequence[date],
) -> dict[int, list[ResolvedSessionPrice]]:
    sessions = list(official_sessions)
    if not sessions:
        return {}

    etf_ids = [etf.id for etf in active_etfs if etf.id is not None]
    raw_panel = load_price_panel(
        session,
        etf_ids=etf_ids,
        start_date=sessions[0],
        end_date=sessions[-1],
    )
    statuses = _load_statuses(
        session,
        etf_ids=etf_ids,
        start_date=sessions[0],
        end_date=sessions[-1],
    )
    statuses_by_etf = {
        etf_id: [status for status in statuses if status.etf_id == etf_id] for etf_id in etf_ids
    }
    required_set = set(sessions)
    resolved: dict[int, list[ResolvedSessionPrice]] = {}

    for etf in active_etfs:
        if etf.id is None:
            raise ValueError("active ETF ids are required for session resolution")
        etf_sessions = list(sessions)
        etf_raw = list(raw_panel.get(etf.id, ()))
        etf_statuses = list(statuses_by_etf.get(etf.id, ()))
        listed_sessions = (
            etf_sessions
            if etf.listing_date is None
            else [value for value in etf_sessions if value >= etf.listing_date]
        )
        if listed_sessions and _has_status_without_raw(
            listed_sessions[0], raw_prices=etf_raw, statuses=etf_statuses
        ):
            _prepend_carry_anchor(
                session,
                etf=etf,
                before_date=listed_sessions[0],
                sessions=etf_sessions,
                raw_prices=etf_raw,
                statuses=etf_statuses,
            )

        etf_resolved = resolve_session_prices(
            official_sessions=etf_sessions,
            active_etfs=[etf],
            raw_prices={etf.id: etf_raw},
            session_statuses={etf.id: etf_statuses},
        )[etf.id]
        resolved[etf.id] = [point for point in etf_resolved if point.trade_date in required_set]

    return resolved


def _prepend_carry_anchor(
    session: Session,
    *,
    etf: ETFInfo,
    before_date: date,
    sessions: list[date],
    raw_prices: list[MarketPrice],
    statuses: list[ETFSessionStatus],
) -> None:
    cursor = before_date
    while True:
        query = (
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date < cursor)
            .order_by(TradingCalendar.trade_date.desc())
            .limit(1)
        )
        if etf.listing_date is not None:
            query = query.where(TradingCalendar.trade_date >= etf.listing_date)
        anchor_date = session.scalar(query)
        if anchor_date is None:
            return

        sessions.insert(0, anchor_date)
        anchor_raw = list(
            session.scalars(
                select(MarketPrice).where(
                    MarketPrice.etf_id == etf.id,
                    MarketPrice.trade_date == anchor_date,
                )
            )
        )
        anchor_statuses = list(
            session.scalars(
                select(ETFSessionStatus).where(
                    ETFSessionStatus.etf_id == etf.id,
                    ETFSessionStatus.trade_date == anchor_date,
                )
            )
        )
        raw_prices.extend(anchor_raw)
        statuses.extend(anchor_statuses)
        if anchor_raw or not anchor_statuses:
            return
        cursor = anchor_date


def _has_status_without_raw(
    trade_date: date,
    *,
    raw_prices: Sequence[MarketPrice],
    statuses: Sequence[ETFSessionStatus],
) -> bool:
    return any(item.trade_date == trade_date for item in statuses) and not any(
        item.trade_date == trade_date for item in raw_prices
    )


def _load_statuses(
    session: Session,
    *,
    etf_ids: list[int],
    start_date: date,
    end_date: date,
) -> list[ETFSessionStatus]:
    if not etf_ids:
        return []
    return list(
        session.scalars(
            select(ETFSessionStatus)
            .where(ETFSessionStatus.etf_id.in_(etf_ids))
            .where(ETFSessionStatus.trade_date >= start_date)
            .where(ETFSessionStatus.trade_date <= end_date)
            .order_by(ETFSessionStatus.etf_id, ETFSessionStatus.trade_date)
        )
    )
