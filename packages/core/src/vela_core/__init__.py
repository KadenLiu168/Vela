from vela_core.akshare_market_data_provider import (
    AkShareMarketDataProvider,
    MarketDataProviderError,
)
from vela_core.app_config import AppConfig, load_app_config
from vela_core.config import (
    ConfigError,
    ETFConfig,
    ETFPoolConfig,
    load_etf_pool_config,
)
from vela_core.market_data_fetcher import (
    MarketDataFetchResult,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
)
from vela_core.market_data_provider import DailyPrice, MarketDataProvider
from vela_core.market_price_mapping import to_market_price
from vela_core.market_price_moving_average import (
    MarketPriceMovingAverage,
    calculate_market_price_moving_average,
)
from vela_core.market_price_returns import (
    MarketPriceReturns,
    calculate_market_price_returns,
)
from vela_core.market_price_upsert import MarketPriceUpsertResult, upsert_market_prices
from vela_core.momentum_scoring import (
    DefensiveFallbackSelection,
    MomentumRanking,
    MomentumScore,
    TopNSelection,
    calculate_momentum_score,
    rank_momentum_scores,
    select_top_n_etfs,
    select_with_defensive_fallback,
)
from vela_core.portfolio_holdings import (
    PortfolioHolding,
    PortfolioHoldingSnapshot,
    calculate_portfolio_holdings,
)
from vela_core.rebalance_dates import generate_weekly_rebalance_dates
from vela_core.strategy_equity_curve import (
    StrategyEquityCurvePoint,
    calculate_strategy_equity_curve,
)
from vela_core.strategy_signal_generation import (
    GeneratedSignalPosition,
    GenerateStrategySignalResult,
    generate_historical_strategy_signals,
    generate_strategy_signal,
)
from vela_core.strategy_signal_persistence import (
    StrategySignalPersistenceResult,
    StrategySignalPositionInput,
    get_latest_successful_strategy_signal,
    persist_strategy_signal,
)
from vela_core.strategy_signal_report import (
    LatestStrategySignalReportNotFoundError,
    StrategySignalReport,
    StrategySignalReportPosition,
    export_latest_strategy_signal_report,
)
from vela_core.trend_filter import TrendFilterResult, apply_trend_filter

__version__ = "0.1.0"

__all__ = [
    "AkShareMarketDataProvider",
    "AppConfig",
    "ConfigError",
    "DailyPrice",
    "DefensiveFallbackSelection",
    "ETFConfig",
    "ETFPoolConfig",
    "GeneratedSignalPosition",
    "GenerateStrategySignalResult",
    "MarketDataProvider",
    "MarketDataProviderError",
    "MarketDataFetchResult",
    "MarketPriceMovingAverage",
    "MarketPriceReturns",
    "MarketPriceUpsertResult",
    "MomentumRanking",
    "MomentumScore",
    "PortfolioHolding",
    "PortfolioHoldingSnapshot",
    "LatestStrategySignalReportNotFoundError",
    "StrategyEquityCurvePoint",
    "StrategySignalPersistenceResult",
    "StrategySignalPositionInput",
    "StrategySignalReport",
    "StrategySignalReportPosition",
    "TopNSelection",
    "TrendFilterResult",
    "apply_trend_filter",
    "calculate_market_price_moving_average",
    "calculate_market_price_returns",
    "calculate_momentum_score",
    "calculate_portfolio_holdings",
    "calculate_strategy_equity_curve",
    "fetch_full_market_prices",
    "fetch_incremental_market_prices",
    "generate_historical_strategy_signals",
    "generate_weekly_rebalance_dates",
    "get_latest_successful_strategy_signal",
    "generate_strategy_signal",
    "export_latest_strategy_signal_report",
    "load_app_config",
    "load_etf_pool_config",
    "persist_strategy_signal",
    "rank_momentum_scores",
    "select_with_defensive_fallback",
    "select_top_n_etfs",
    "to_market_price",
    "upsert_market_prices",
    "__version__",
]
