from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from vela_core.config import ETFConfig
from vela_core.strategy_config import StrategyConfig


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ResponseModel):
    status: str


class ConfigResponse(ResponseModel):
    strategy: StrategyConfig
    etf_pool: "EtfPoolResponse"


class EtfPoolResponse(ResponseModel):
    pool_id: str
    version: int
    description: str | None
    provider: str
    currency: str
    total_etfs: int
    active_etfs: int
    etfs: list[ETFConfig]


class DashboardMarketDataEtfResponse(ResponseModel):
    etf_id: int
    exchange: str
    symbol: str
    name: str
    category: str | None
    earliest_trade_date: date | None


class DashboardMarketDataResponse(ResponseModel):
    price_rows: int
    covered_etfs: int
    earliest_trade_date: date | None
    latest_trade_date: date | None
    etf_list: list[DashboardMarketDataEtfResponse]


class DashboardSignalResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    status: str
    result: str | None
    generated_at: datetime
    is_fallback: bool
    position_count: int


class DashboardBacktestResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    total_return: str | None
    max_drawdown: str | None
    sharpe_ratio: str | None
    started_at: datetime


class DashboardFetchLogResponse(ResponseModel):
    fetch_log_id: int
    fetch_time: datetime
    mode: str
    status: str
    rows_fetched: int | None
    rows_inserted: int | None
    rows_updated: int | None
    error_summary: str | None


class DashboardResponse(ResponseModel):
    strategy: StrategyConfig
    market_data: DashboardMarketDataResponse
    latest_signal: DashboardSignalResponse | None
    recent_backtest: DashboardBacktestResponse | None
    recent_fetch_logs: list[DashboardFetchLogResponse]


class EtfResponse(ResponseModel):
    id: int
    exchange: str
    symbol: str
    name: str


class EtfPricePointResponse(ResponseModel):
    trade_date: date
    price: str


class EtfPriceTrendResponse(ResponseModel):
    etf: EtfResponse
    points: list[EtfPricePointResponse]


class MarketDataFetchResponse(ResponseModel):
    status: str
    requested_etf_count: int
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    failed_symbols: list[str]
    error_message: str | None


class BootstrapStepResponse(ResponseModel):
    name: str
    status: str
    duration_seconds: float
    error_message: str | None


class BootstrapResponse(ResponseModel):
    status: str
    failed_step: str | None
    total_duration_seconds: float
    steps: list[BootstrapStepResponse]


class GeneratedPositionResponse(ResponseModel):
    etf_id: int
    exchange: str
    symbol: str
    target_weight: str | None
    rank: int | None
    score: str | None


class GenerateSignalResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    status: str
    result: str | None
    error_message: str | None
    source: str
    positions: list[GeneratedPositionResponse]


class SignalMetadataResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    generated_at: datetime
    result: str
    is_fallback: bool


class SignalPositionResponse(ResponseModel):
    exchange: str
    symbol: str
    name: str
    target_weight: str | None
    rank: int | None
    score: str | None
    is_fallback: bool


class LatestSignalResponse(ResponseModel):
    has_signal: bool
    signal: SignalMetadataResponse | None
    positions: list[SignalPositionResponse]


class SignalListItemResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    result: str
    generated_at: datetime
    is_fallback: bool
    position_count: int
    source: str
    backtest_run_id: int | None


class SignalListResponse(ResponseModel):
    signals: list[SignalListItemResponse]


class SignalDetailMetadataResponse(SignalMetadataResponse):
    strategy_id: str
    source: str
    backtest_run_id: int | None


class SignalDetailResponse(ResponseModel):
    signal: SignalDetailMetadataResponse
    positions: list[SignalPositionResponse]


class BacktestMetricsResponse(ResponseModel):
    total_return: str | None
    annualized_return: str | None
    max_drawdown: str | None
    volatility: str | None
    sharpe_ratio: str | None


class BacktestRunResponse(BacktestMetricsResponse):
    run_id: int
    status: str
    start_date: date
    end_date: date
    trading_day_count: int
    signal_count: int
    benchmarks: list["BacktestBenchmarkResponse"]


class BacktestListItemResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    started_at: datetime
    finished_at: datetime | None
    total_return: str | None
    annualized_return: str | None
    max_drawdown: str | None
    volatility: str | None
    sharpe_ratio: str | None


class BacktestListResponse(ResponseModel):
    runs: list[BacktestListItemResponse]


class BacktestDetailRunResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    parameters_json: str
    status: str
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class EquityCurvePointResponse(ResponseModel):
    trade_date: date
    net_value: str | None
    cash: str | None
    market_value: str | None
    total_assets: str | None
    positions_json: str


class BacktestBenchmarkCurvePointResponse(ResponseModel):
    trade_date: date
    net_value: str


class BacktestBenchmarkResponse(BacktestMetricsResponse):
    key: str
    name: str
    total_return_difference: str | None
    annualized_return_difference: str | None
    equity_curve: list[BacktestBenchmarkCurvePointResponse] = []


class BacktestDetailResponse(ResponseModel):
    run: BacktestDetailRunResponse
    metrics: BacktestMetricsResponse
    equity_curve: list[EquityCurvePointResponse]
    signal_ids: list[int]
    signal_count: int
    benchmarks: list[BacktestBenchmarkResponse]


class BacktestSignalSummaryResponse(ResponseModel):
    signal_id: int
    signal_date: date
    result: str
    backtest_run_id: int


class BacktestSignalsResponse(ResponseModel):
    signals: list[BacktestSignalSummaryResponse]
