import { useEffect, useState } from "react";
import {
  ApiClientError,
  type DashboardBacktestSummary,
  type DashboardFetchLogSummary,
  type DashboardResponse,
  type DashboardSignalSummary,
  type LatestStrategySignalResponse,
  type MarketDataFetchResponse,
  type StrategySignalGenerationResponse,
  fetchFullMarketData,
  fetchIncrementalMarketData,
  generateStrategySignal,
  getDashboard,
  getLatestStrategySignal
} from "../api/client";

type DashboardState =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: DashboardResponse; error?: never }
  | { status: "error"; data?: never; error: string };

type MarketDataFetchMode = "incremental" | "full";
type OperationError =
  | { operation: "marketDataFetch"; kind: string }
  | { operation: "signalGeneration"; kind: string };

export function DashboardPage() {
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    status: "loading"
  });
  const [marketDataFetchMode, setMarketDataFetchMode] = useState<MarketDataFetchMode | null>(null);
  const [isGeneratingSignal, setIsGeneratingSignal] = useState(false);
  const [operationError, setOperationError] = useState<OperationError | null>(null);
  const [marketDataFetchResult, setMarketDataFetchResult] = useState<MarketDataFetchResponse | null>(null);
  const [signalGenerationResult, setSignalGenerationResult] =
    useState<StrategySignalGenerationResponse | null>(null);

  useEffect(() => {
    let isCurrent = true;

    loadDashboard((nextState) => {
      if (isCurrent) {
        setDashboardState(nextState);
      }
    });

    return () => {
      isCurrent = false;
    };
  }, []);

  async function handleMarketDataFetch(mode: MarketDataFetchMode) {
    if (marketDataFetchMode) {
      return;
    }

    setMarketDataFetchMode(mode);
    setOperationError(null);

    try {
      const fetchResult = await (mode === "full" ? fetchFullMarketData() : fetchIncrementalMarketData());
      setMarketDataFetchResult(fetchResult);
      setSignalGenerationResult(null);
      await loadDashboard(setDashboardState);
    } catch (error: unknown) {
      setMarketDataFetchResult(null);
      setOperationError({
        operation: "marketDataFetch",
        kind: error instanceof ApiClientError ? error.kind : "unavailable"
      });
    } finally {
      setMarketDataFetchMode(null);
    }
  }

  async function handleSignalGeneration() {
    if (isGeneratingSignal) {
      return;
    }

    setIsGeneratingSignal(true);
    setOperationError(null);

    try {
      const generationResult = await generateStrategySignal();
      setSignalGenerationResult(generationResult);
      setMarketDataFetchResult(null);
      await refreshDashboardSignalState(generationResult, setDashboardState);
    } catch (error: unknown) {
      setSignalGenerationResult(null);
      setOperationError({
        operation: "signalGeneration",
        kind: error instanceof ApiClientError ? error.kind : "unavailable"
      });
    } finally {
      setIsGeneratingSignal(false);
    }
  }

  const data = dashboardState.status === "ready" ? dashboardState.data : undefined;
  const marketFetchAction = {
    isLoading: marketDataFetchMode !== null,
    onClick: () => {
      void handleMarketDataFetch("incremental");
    }
  };
  const signalGenerationAction = {
    isLoading: isGeneratingSignal,
    onClick: () => {
      void handleSignalGeneration();
    }
  };

  return (
    <section className="page dashboard-page">
      <div className="page-heading dashboard-heading">
        <div>
          <p>Local research workflow</p>
          <h2>Workflow Dashboard</h2>
        </div>
        <span className={`dashboard-load-state dashboard-load-state-${dashboardState.status}`}>
          {getLoadLabel(dashboardState)}
        </span>
      </div>

      {dashboardState.status === "error" ? (
        <p className="dashboard-alert">Dashboard API unavailable: {dashboardState.error}</p>
      ) : null}

      <div className="dashboard-grid" aria-label="Dashboard workflow summary">
        <article className="dashboard-panel market-panel">
          <PanelHeading eyebrow="Market" title="Market data" />
          <div className="metric-row">
            <Metric
              label="Price rows"
              value={data ? `${formatNumber(data.market_data.price_rows)} rows` : "Loading"}
            />
            <Metric
              label="Covered ETFs"
              value={data ? `${formatNumber(data.market_data.covered_etfs)} ETFs` : "Loading"}
            />
          </div>
          {data?.market_data.price_rows === 0 ? (
            <EmptyAction
              actionLabel="Fetch market data"
              className="market-empty-state"
              isLoading={marketFetchAction.isLoading}
              message="No local market prices are stored yet. Fetch market data to populate dashboard coverage."
              onClick={marketFetchAction.onClick}
            />
          ) : null}
          <dl className="compact-list">
            <Detail label="Earliest trade date" value={formatOptional(data?.market_data.earliest_trade_date)} />
            <Detail label="Latest trade date" value={formatOptional(data?.market_data.latest_trade_date)} />
          </dl>
        </article>

        <article className="dashboard-panel strategy-panel">
          <PanelHeading eyebrow="Strategy" title="Strategy summary" />
          <strong className="panel-primary">{data?.strategy.strategy_id ?? "Loading"}</strong>
          <dl className="compact-list">
            <Detail label="Version" value={data?.strategy.version ?? "Loading"} />
            <Detail
              label="Momentum windows"
              value={data ? formatMomentumWindows(data.strategy.momentum) : "Loading"}
            />
            <Detail
              label="Score weights"
              value={data ? formatScoreWeights(data.strategy.score_weights) : "Loading"}
            />
            <Detail label="Top N" value={data ? formatNumber(data.strategy.selection.top_n) : "Loading"} />
            <Detail
              label="Defensive asset"
              value={data ? formatDefensiveAsset(data.strategy.defense.asset) : "Loading"}
            />
            <Detail
              label="Trading cost"
              value={data ? `${formatCompactNumber(data.strategy.costs.transaction_cost_bps)} bps` : "Loading"}
            />
            <Detail label="Universe" value={data?.strategy.universe_config ?? "Loading"} />
          </dl>
        </article>

        <article className="dashboard-panel signal-panel">
          <PanelHeading eyebrow="Signal" title="Latest signal" />
          <SignalSummary
            signal={data?.latest_signal}
            isGeneratingSignal={signalGenerationAction.isLoading}
            isLoading={dashboardState.status === "loading"}
            onGenerateSignal={signalGenerationAction.onClick}
          />
        </article>

        <article className="dashboard-panel backtest-panel">
          <PanelHeading eyebrow="Backtest" title="Recent backtest" />
          <BacktestSummary
            backtest={data?.recent_backtest}
            isLoading={dashboardState.status === "loading"}
          />
        </article>

        <article className="dashboard-panel fetch-log-panel">
          <PanelHeading eyebrow="History" title="Recent fetches" />
          <FetchLogSummary logs={data?.recent_fetch_logs} isLoading={dashboardState.status === "loading"} />
        </article>

        <article className="dashboard-panel operations-panel">
          <PanelHeading eyebrow="Actions" title="Operations" />
          {operationError ? (
            <p className="dashboard-alert operation-alert">{formatOperationError(operationError)}</p>
          ) : null}
          {marketDataFetchResult ? <MarketDataFetchSummary result={marketDataFetchResult} /> : null}
          {signalGenerationResult ? <SignalGenerationSummary result={signalGenerationResult} /> : null}
          <div className="operation-list">
            <button type="button" disabled={marketFetchAction.isLoading} onClick={marketFetchAction.onClick}>
              {marketDataFetchMode === "incremental" ? "Fetching market data" : "Fetch market data"}
            </button>
            <button
              type="button"
              disabled={marketFetchAction.isLoading}
              onClick={() => {
                void handleMarketDataFetch("full");
              }}
            >
              {marketDataFetchMode === "full" ? "Running full fetch" : "Full fetch for initialization or repair"}
            </button>
            <button
              type="button"
              disabled={signalGenerationAction.isLoading}
              onClick={signalGenerationAction.onClick}
            >
              {signalGenerationAction.isLoading ? "Generating signal" : "Generate signal"}
            </button>
            <button type="button" disabled>
              Run backtest
            </button>
          </div>
        </article>
      </div>
    </section>
  );
}

function SignalGenerationSummary({ result }: { result: StrategySignalGenerationResponse }) {
  return (
    <div className={`operation-summary operation-summary-${result.status}`} aria-live="polite">
      <strong>Signal generation {result.status}</strong>
      <dl className="compact-list">
        <Detail label="Signal" value={`#${formatNumber(result.signal_id)}`} />
        <Detail label="Signal date" value={result.signal_date} />
        <Detail label="Result" value={formatOptional(result.result)} />
        <Detail label="Positions" value={formatNumber(result.positions.length)} />
      </dl>
      {result.error_message ? <p className="operation-guidance">{result.error_message}</p> : null}
    </div>
  );
}

function MarketDataFetchSummary({ result }: { result: MarketDataFetchResponse }) {
  const hasFailures = result.status === "partial" || result.status === "failed";

  return (
    <div className={`operation-summary operation-summary-${result.status}`} aria-live="polite">
      <strong>Market data fetch {result.status}</strong>
      <dl className="compact-list">
        <Detail label="Fetched" value={`${formatNumber(result.rows_fetched)} rows`} />
        <Detail label="Inserted" value={`${formatNumber(result.rows_inserted)} rows`} />
        <Detail label="Updated" value={`${formatNumber(result.rows_updated)} rows`} />
        {hasFailures ? (
          <>
            <Detail label="Failed symbols" value={formatFailedSymbols(result.failed_symbols)} />
            <Detail label="Error summary" value={formatOptional(result.error_message)} />
          </>
        ) : null}
      </dl>
      {hasFailures ? (
        <p className="operation-guidance">
          Retry the fetch after checking the data source availability and local ETF/data state.
        </p>
      ) : null}
    </div>
  );
}

function FetchLogSummary({
  isLoading,
  logs
}: {
  isLoading: boolean;
  logs: DashboardFetchLogSummary[] | undefined;
}) {
  if (isLoading) {
    return <p className="empty-state">Loading fetch history.</p>;
  }

  if (!logs || logs.length === 0) {
    return <p className="empty-state">No market data fetch history exists yet.</p>;
  }

  return (
    <div className="fetch-log-list">
      {logs.map((log) => (
        <dl className="compact-list fetch-log-entry" key={log.fetch_log_id}>
          <Detail label="Fetch time" value={log.fetch_time} />
          <Detail label="Mode" value={log.mode} />
          <Detail label="Status" value={log.status} />
          <Detail label="Fetched" value={formatOptionalRows(log.rows_fetched)} />
          <Detail label="Inserted" value={formatOptionalRows(log.rows_inserted)} />
          <Detail label="Updated" value={formatOptionalRows(log.rows_updated)} />
          <Detail label="Error summary" value={formatOptional(log.error_summary)} />
        </dl>
      ))}
    </div>
  );
}

function SignalSummary({
  isGeneratingSignal,
  isLoading,
  onGenerateSignal,
  signal
}: {
  isGeneratingSignal: boolean;
  isLoading: boolean;
  onGenerateSignal: () => void;
  signal: DashboardSignalSummary | null | undefined;
}) {
  if (isLoading) {
    return <p className="empty-state">Loading latest signal.</p>;
  }

  if (!signal) {
    return (
      <EmptyAction
        actionLabel="Generate signal"
        className="signal-empty-action"
        isLoading={isGeneratingSignal}
        loadingLabel="Generating signal"
        message="No successful local signal exists yet. Generate signal after market data is ready."
        onClick={onGenerateSignal}
      />
    );
  }

  return (
    <>
      <strong className="panel-primary">Signal #{signal.signal_id}</strong>
      <dl className="compact-list">
        <Detail label="Signal date" value={signal.signal_date} />
        <Detail label="Status" value={signal.status} />
        <Detail label="Result" value={formatOptional(signal.result)} />
        <Detail label="Fallback" value={formatBoolean(signal.is_fallback)} />
        <Detail label="Target holdings" value={formatNumber(signal.position_count)} />
      </dl>
    </>
  );
}

function BacktestSummary({
  backtest,
  isLoading
}: {
  backtest: DashboardBacktestSummary | null | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return <p className="empty-state">Loading recent backtest.</p>;
  }

  if (!backtest) {
    return (
      <EmptyAction
        actionLabel="Run backtest"
        className="backtest-empty-action"
        message="No local backtest run exists yet. Run backtest after a signal is available."
      />
    );
  }

  return (
    <>
      <strong className="panel-primary">Backtest #{backtest.run_id}</strong>
      <dl className="compact-list">
        <Detail label="Range" value={`${backtest.start_date} to ${backtest.end_date}`} />
        <Detail label="Status" value={backtest.status} />
        <Detail label="Total return" value={formatPercent(backtest.total_return)} />
        <Detail label="Max drawdown" value={formatPercent(backtest.max_drawdown)} />
        <Detail label="Sharpe" value={formatOptional(backtest.sharpe_ratio)} />
      </dl>
    </>
  );
}

function PanelHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="panel-heading">
      <span>{eyebrow}</span>
      <h3>{title}</h3>
    </div>
  );
}

function EmptyAction({
  actionLabel,
  className,
  isLoading = false,
  loadingLabel,
  message,
  onClick
}: {
  actionLabel: string;
  className?: string;
  isLoading?: boolean;
  loadingLabel?: string;
  message: string;
  onClick?: () => void;
}) {
  return (
    <div className={className}>
      <p className="empty-state">{message}</p>
      <div className="operation-list empty-action">
        <button type="button" disabled={isLoading || !onClick} onClick={onClick}>
          {isLoading ? (loadingLabel ?? actionLabel) : actionLabel}
        </button>
      </div>
    </div>
  );
}

async function loadDashboard(setState: (state: DashboardState) => void) {
  try {
    const dashboard = await getDashboard();
    setState({ status: "ready", data: dashboard });
  } catch (error: unknown) {
    setState({
      status: "error",
      error: error instanceof ApiClientError ? error.kind : "unavailable"
    });
  }
}

async function refreshDashboardSignalState(
  generationResult: StrategySignalGenerationResponse,
  setState: (state: DashboardState) => void
) {
  const [dashboard, latestSignal] = await Promise.all([getDashboard(), getLatestStrategySignal()]);
  setState({
    status: "ready",
    data: backfillLatestSignalSummary(dashboard, latestSignal, generationResult)
  });
}

function backfillLatestSignalSummary(
  dashboard: DashboardResponse,
  latestSignal: LatestStrategySignalResponse,
  generationResult: StrategySignalGenerationResponse
): DashboardResponse {
  if (!latestSignal.has_signal || latestSignal.signal === null) {
    return dashboard;
  }

  return {
    ...dashboard,
    latest_signal: {
      signal_id: latestSignal.signal.signal_id,
      signal_date: latestSignal.signal.signal_date,
      config_version: latestSignal.signal.config_version,
      status: generationResult.status,
      result: latestSignal.signal.result,
      generated_at: latestSignal.signal.generated_at,
      is_fallback: latestSignal.signal.is_fallback,
      position_count: latestSignal.positions.length
    }
  };
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

function getLoadLabel(state: DashboardState): string {
  if (state.status === "loading") {
    return "Loading dashboard";
  }

  if (state.status === "error") {
    return "API unavailable";
  }

  return "Dashboard loaded";
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(value);
}

function formatMomentumWindows(momentum: DashboardResponse["strategy"]["momentum"]): string {
  return `${formatNumber(momentum.short_window_days)} / ${formatNumber(momentum.long_window_days)} days`;
}

function formatScoreWeights(scoreWeights: DashboardResponse["strategy"]["score_weights"]): string {
  return `Short ${formatCompactNumber(scoreWeights.short)} / Long ${formatCompactNumber(scoreWeights.long)}`;
}

function formatDefensiveAsset(asset: DashboardResponse["strategy"]["defense"]["asset"]): string {
  return `${asset.exchange}:${asset.symbol}`;
}

function formatOptional(value: string | null | undefined): string {
  return value ?? "Not available";
}

function formatOptionalRows(value: number | null): string {
  return value === null ? "Not available" : `${formatNumber(value)} rows`;
}

function formatFailedSymbols(symbols: string[]): string {
  return symbols.length > 0 ? symbols.join(", ") : "Not available";
}

function formatBoolean(value: boolean): string {
  return value ? "Yes" : "No";
}

function formatOperationError(error: OperationError): string {
  const operationLabel =
    error.operation === "signalGeneration" ? "Signal generation" : "Market data fetch";
  return `${operationLabel} failed: ${error.kind}`;
}

function formatPercent(value: string | null): string {
  if (value === null) {
    return "Not available";
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(2)}%` : value;
}
