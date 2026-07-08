from vela_core.akshare_market_data_provider import (
    AkShareMarketDataProvider,
    MarketDataProviderError,
)
from vela_core.app_config import AppConfig, load_app_config
from vela_core.backtest_report import BacktestReportNotFoundError, export_backtest_report
from vela_core.backtest_result_persistence import (
    BacktestEquityCurveInput,
    BacktestResultPersistenceResult,
    BacktestResultRunInput,
    get_backtest_result,
    persist_backtest_result,
)
from vela_core.backtest_runner import BacktestRunResult, run_backtest
from vela_core.bootstrap import (
    BootstrapResult,
    BootstrapStepResult,
    run_local_setup_bootstrap,
)
from vela_core.config import (
    ConfigError,
    ETFConfig,
    ETFPoolConfig,
    load_etf_pool_config,
)
from vela_core.dashboard_aggregation import (
    DashboardBacktestSummary,
    DashboardMarketDataStatus,
    DashboardSignalSummary,
    get_dashboard_summary,
)
from vela_core.etf_pool_sync import ETFPoolSyncResult, sync_etf_pool_to_db
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
from vela_core.rebalance_dates import (
    RebalanceFrequency,
    generate_monthly_rebalance_dates,
    generate_rebalance_dates,
    generate_weekly_rebalance_dates,
)
from vela_core.strategy_equity_curve import (
    StrategyAnnualizedReturn,
    StrategyEquityCurvePoint,
    StrategyMaximumDrawdown,
    StrategySharpeRatio,
    StrategyVolatility,
    calculate_strategy_annualized_return,
    calculate_strategy_equity_curve,
    calculate_strategy_maximum_drawdown,
    calculate_strategy_sharpe_ratio,
    calculate_strategy_volatility,
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
    StrategySignalListEntry,
    StrategySignalReport,
    StrategySignalReportPosition,
    export_latest_strategy_signal_report,
    get_latest_strategy_signal_report,
    get_strategy_signal_report,
    list_strategy_signals,
)
from vela_core.tencent_market_data_provider import TencentMarketDataProvider
from vela_core.trend_filter import TrendFilterResult, apply_trend_filter

__version__ = "0.1.0"

__all__ = [
    "AkShareMarketDataProvider",
    "AppConfig",
    "BacktestEquityCurveInput",
    "BacktestResultPersistenceResult",
    "BacktestResultRunInput",
    "BacktestReportNotFoundError",
    "BacktestRunResult",
    "BootstrapResult",
    "BootstrapStepResult",
    "ConfigError",
    "DailyPrice",
    "DashboardBacktestSummary",
    "DashboardMarketDataStatus",
    "DashboardSignalSummary",
    "DefensiveFallbackSelection",
    "ETFConfig",
    "ETFPoolConfig",
    "ETFPoolSyncResult",
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
    "RebalanceFrequency",
    "LatestStrategySignalReportNotFoundError",
    "StrategyEquityCurvePoint",
    "StrategyAnnualizedReturn",
    "StrategyMaximumDrawdown",
    "StrategySharpeRatio",
    "StrategyVolatility",
    "StrategySignalPersistenceResult",
    "TencentMarketDataProvider",
    "StrategySignalListEntry",
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
    "calculate_strategy_annualized_return",
    "calculate_strategy_equity_curve",
    "calculate_strategy_maximum_drawdown",
    "calculate_strategy_sharpe_ratio",
    "calculate_strategy_volatility",
    "fetch_full_market_prices",
    "fetch_incremental_market_prices",
    "get_backtest_result",
    "get_dashboard_summary",
    "generate_historical_strategy_signals",
    "generate_monthly_rebalance_dates",
    "generate_rebalance_dates",
    "generate_weekly_rebalance_dates",
    "get_latest_successful_strategy_signal",
    "get_latest_strategy_signal_report",
    "get_strategy_signal_report",
    "generate_strategy_signal",
    "list_strategy_signals",
    "export_latest_strategy_signal_report",
    "export_backtest_report",
    "load_app_config",
    "load_etf_pool_config",
    "persist_strategy_signal",
    "persist_backtest_result",
    "rank_momentum_scores",
    "run_backtest",
    "run_local_setup_bootstrap",
    "select_with_defensive_fallback",
    "select_top_n_etfs",
    "sync_etf_pool_to_db",
    "to_market_price",
    "upsert_market_prices",
    "__version__",
]
