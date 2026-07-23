from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, MarketPrice, StrategySignal
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


def generate_and_persist_strategy_signal(
    session: Session,
    *,
    config: StrategyConfig,
    signal_date: date | None = None,
    source: str = "manual",
) -> GenerateStrategySignalResult:
    if source not in StrategySignal.LIVE_SOURCES:
        raise ValueError(f"Unsupported live strategy signal source: {source}")
    resolved_signal_date = signal_date or session.scalar(select(func.max(MarketPrice.trade_date)))
    if resolved_signal_date is None:
        raise ValueError("No local market prices found")

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

    return generate_strategy_signal(
        signal_date=resolved_signal_date,
        config=config,
        price_panel=price_panel,
        active_etfs=active_etfs,
        persist=_persist,
    )
