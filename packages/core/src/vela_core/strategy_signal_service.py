import logging
import time
from datetime import date
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vela_core.errors import MissingMarketDataError
from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, MarketPrice, StrategySignal
from vela_core.resolved_session_price import ResolvedSessionPrice
from vela_core.strategy_config import StrategyConfig
from vela_core.strategy_signal_generation import (
    GenerateStrategySignalResult,
    PersistStrategySignalPosition,
    generate_strategy_signal,
)
from vela_core.strategy_signal_persistence import (
    StrategySignalPositionInput,
    persist_strategy_signal,
)

logger = logging.getLogger(__name__)


def generate_and_persist_strategy_signal(
    session: Session,
    *,
    config: StrategyConfig,
    signal_date: date | None = None,
    source: str = "manual",
) -> GenerateStrategySignalResult:
    started = time.perf_counter()
    logger.info(
        "strategy_signal.current.started strategy_id=%s signal_date=%s",
        config.strategy_id,
        signal_date.isoformat() if signal_date is not None else "latest",
    )
    if source not in StrategySignal.LIVE_SOURCES:
        raise ValueError(f"Unsupported live strategy signal source: {source}")
    resolved_signal_date = signal_date or session.scalar(select(func.max(MarketPrice.trade_date)))
    if resolved_signal_date is None:
        raise MissingMarketDataError("No local market prices found")

    active_etfs = list(
        session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.id))
    )
    price_panel = load_price_panel(
        session,
        etf_ids=[etf.id for etf in active_etfs],
        start_date=None,
        end_date=resolved_signal_date,
    )

    def _persist(
        *,
        signal_date: date,
        generated_at,
        status: str,
        result: str | None,
        positions: list[PersistStrategySignalPosition],
        error_message: str | None,
    ) -> int:
        persistence_result = persist_strategy_signal(
            session,
            strategy_id=config.strategy_id,
            signal_date=signal_date,
            config_version=config.version,
            generated_at=generated_at,
            status=status,
            result=result,
            source=source,
            backtest_run_id=None,
            positions=[
                StrategySignalPositionInput(
                    etf_id=position["etf_id"],
                    rank=position["rank"],
                    score=position["score"],
                    target_weight=position["target_weight"],
                )
                for position in positions
            ],
            error_message=error_message,
        )
        session.commit()
        return persistence_result.strategy_signal.id

    result = generate_strategy_signal(
        signal_date=resolved_signal_date,
        config=config,
        price_panel=cast(dict[int, list[MarketPrice | ResolvedSessionPrice]], price_panel),
        active_etfs=active_etfs,
        persist=_persist,
    )
    logger.info(
        "strategy_signal.current.completed strategy_id=%s signal_date=%s status=%s "
        "position_count=%s duration_ms=%.3f",
        config.strategy_id,
        result.signal_date.isoformat(),
        result.status,
        len(result.positions),
        (time.perf_counter() - started) * 1000,
    )
    return result
