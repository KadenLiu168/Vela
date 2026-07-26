from vela_core.app_config import AppConfig, load_app_config
from vela_core.backtest_report import BacktestReportNotFoundError, export_backtest_report
from vela_core.backtest_result_persistence import (
    BacktestEquityCurveInput,
    BacktestResultPersistenceResult,
    BacktestResultRunInput,
    get_backtest_result,
    persist_backtest_result,
)
from vela_core.backtest_runner import BacktestGapDetectionConfig, BacktestRunResult, run_backtest
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
from vela_core.data_quality import (
    CorporateActionFactorMismatchWarning,
    DuplicateTradeDateWarning,
    EtfTradingDayGap,
    SystematicTradingDayGap,
    build_quality_warnings_json,
    build_quality_warnings_json_from_sections,
    detect_corporate_action_factor_mismatch,
    detect_duplicate_trade_dates,
    detect_etf_trading_day_gaps,
    detect_systematic_trading_day_gaps,
)
from vela_core.etf_pool_sync import ETFPoolSyncResult, sync_etf_pool_to_db
from vela_core.etf_price_trend import (
    EtfPriceTrendPoint,
    EtfPriceTrendResult,
    PriceTrendRange,
    get_etf_price_trend,
)
from vela_core.joinquant_market_data_provider import JoinQuantMarketDataProvider
from vela_core.market_data_fetcher import (
    MarketDataFetchResult,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
)
from vela_core.market_data_provider import (
    DailyPrice,
    MarketDataProvider,
    MarketDataProviderError,
)
from vela_core.market_price_mapping import to_market_price
from vela_core.market_price_moving_average import (
    MarketPriceMovingAverage,
    calculate_market_price_moving_average,
)
from vela_core.market_price_query import load_price_panel
from vela_core.market_price_returns import (
    MarketPriceReturns,
    calculate_market_price_returns,
)
from vela_core.market_price_upsert import MarketPriceUpsertResult, upsert_market_prices
from vela_core.migration import build_alembic_config, run_alembic_upgrade
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
    StrategyPortfolioPosition,
    StrategyPortfolioState,
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
    link_signals_to_backtest_run,
    persist_strategy_signal,
)
from vela_core.strategy_signal_report import (
    BacktestSignalSummaryEntry,
    LatestStrategySignalReportNotFoundError,
    StrategySignalListEntry,
    StrategySignalReport,
    StrategySignalReportPosition,
    export_latest_strategy_signal_report,
    get_latest_strategy_signal_report,
    get_strategy_signal_report,
    list_backtest_signals,
    list_strategy_signals,
)
from vela_core.strategy_signal_service import generate_and_persist_strategy_signal
from vela_core.tencent_market_data_provider import TencentMarketDataProvider
from vela_core.trading_calendar_sync import (
    TradingCalendarSyncResult,
    sync_trading_calendar_to_db,
)
from vela_core.trend_filter import TrendFilterResult, apply_trend_filter
from vela_core.walk_forward.config import WalkForwardConfig, load_walk_forward_config
from vela_core.walk_forward.runner import WalkForwardRunner

__version__ = "0.1.0"

__all__ = [
    "AppConfig",
    "BacktestEquityCurveInput",
    "BacktestResultPersistenceResult",
    "BacktestResultRunInput",
    "BacktestReportNotFoundError",
    "BacktestRunResult",
    "BacktestGapDetectionConfig",
    "BacktestSignalSummaryEntry",
    "BootstrapResult",
    "BootstrapStepResult",
    "ConfigError",
    "CorporateActionFactorMismatchWarning",
    "DailyPrice",
    "DashboardBacktestSummary",
    "DashboardMarketDataStatus",
    "DashboardSignalSummary",
    "DefensiveFallbackSelection",
    "DuplicateTradeDateWarning",
    "ETFConfig",
    "ETFPoolConfig",
    "ETFPoolSyncResult",
    "EtfPriceTrendPoint",
    "EtfPriceTrendResult",
    "EtfTradingDayGap",
    "GeneratedSignalPosition",
    "GenerateStrategySignalResult",
    "JoinQuantMarketDataProvider",
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
    "PriceTrendRange",
    "RebalanceFrequency",
    "LatestStrategySignalReportNotFoundError",
    "StrategyEquityCurvePoint",
    "StrategyPortfolioPosition",
    "StrategyPortfolioState",
    "StrategyAnnualizedReturn",
    "StrategyMaximumDrawdown",
    "StrategySharpeRatio",
    "StrategyVolatility",
    "StrategySignalPersistenceResult",
    "link_signals_to_backtest_run",
    "TencentMarketDataProvider",
    "TradingCalendarSyncResult",
    "StrategySignalListEntry",
    "StrategySignalPositionInput",
    "StrategySignalReport",
    "StrategySignalReportPosition",
    "SystematicTradingDayGap",
    "TopNSelection",
    "TrendFilterResult",
    "WalkForwardConfig",
    "WalkForwardRunner",
    "apply_trend_filter",
    "build_alembic_config",
    "build_quality_warnings_json",
    "build_quality_warnings_json_from_sections",
    "calculate_market_price_moving_average",
    "calculate_market_price_returns",
    "calculate_momentum_score",
    "calculate_portfolio_holdings",
    "calculate_strategy_annualized_return",
    "calculate_strategy_equity_curve",
    "calculate_strategy_maximum_drawdown",
    "calculate_strategy_sharpe_ratio",
    "calculate_strategy_volatility",
    "detect_corporate_action_factor_mismatch",
    "detect_duplicate_trade_dates",
    "detect_etf_trading_day_gaps",
    "detect_systematic_trading_day_gaps",
    "fetch_full_market_prices",
    "fetch_incremental_market_prices",
    "get_backtest_result",
    "get_dashboard_summary",
    "get_etf_price_trend",
    "generate_and_persist_strategy_signal",
    "generate_historical_strategy_signals",
    "generate_monthly_rebalance_dates",
    "generate_rebalance_dates",
    "generate_weekly_rebalance_dates",
    "get_latest_successful_strategy_signal",
    "load_price_panel",
    "get_latest_strategy_signal_report",
    "get_strategy_signal_report",
    "generate_strategy_signal",
    "list_backtest_signals",
    "list_strategy_signals",
    "export_latest_strategy_signal_report",
    "export_backtest_report",
    "load_app_config",
    "load_etf_pool_config",
    "load_walk_forward_config",
    "persist_strategy_signal",
    "persist_backtest_result",
    "rank_momentum_scores",
    "run_backtest",
    "run_alembic_upgrade",
    "run_local_setup_bootstrap",
    "select_with_defensive_fallback",
    "select_top_n_etfs",
    "sync_etf_pool_to_db",
    "sync_trading_calendar_to_db",
    "to_market_price",
    "upsert_market_prices",
    "__version__",
]
