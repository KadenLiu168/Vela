import { useEffect, useState } from "react";
import {
  ApiClientError,
  type BacktestRunResponse,
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
  getLatestStrategySignal,
  runBacktest
} from "../api/client";
import { FeedbackMessage } from "../components/FeedbackMessage";
import {
  formatBoolean,
  formatCompactNumber,
  formatDate,
  formatInteger,
  formatNullableText,
  formatRatioAsPercent,
  formatRows
} from "../utils/formatters";

type DashboardState =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: DashboardResponse; error?: never }
  | { status: "error"; data?: never; error: string };

type MarketDataFetchMode = "incremental" | "full";
type ActiveOperation = "backtestRun" | "marketDataFetch" | "signalGeneration";
type OperationError =
  | { operation: "marketDataFetch"; kind: string }
  | { operation: "signalGeneration"; kind: string }
  | { operation: "backtestRun"; kind: string };

type BacktestFormState = {
  startDate: string;
  endDate: string;
};

export function DashboardPage() {
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    status: "loading"
  });
  const [activeOperation, setActiveOperation] = useState<ActiveOperation | null>(null);
  const [marketDataFetchMode, setMarketDataFetchMode] = useState<MarketDataFetchMode | null>(null);
  const [operationError, setOperationError] = useState<OperationError | null>(null);
  const [marketDataFetchResult, setMarketDataFetchResult] = useState<MarketDataFetchResponse | null>(null);
  const [signalGenerationResult, setSignalGenerationResult] =
    useState<StrategySignalGenerationResponse | null>(null);
  const [backtestRunResult, setBacktestRunResult] = useState<BacktestRunResponse | null>(null);
  const [backtestForm, setBacktestForm] = useState<BacktestFormState>({
    startDate: "",
    endDate: ""
  });
  const [backtestValidationError, setBacktestValidationError] = useState<string | null>(null);

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
    if (activeOperation) {
      return;
    }

    setActiveOperation("marketDataFetch");
    setMarketDataFetchMode(mode);
    setOperationError(null);

    try {
      const fetchResult = await (mode === "full" ? fetchFullMarketData() : fetchIncrementalMarketData());
      setMarketDataFetchResult(fetchResult);
      setSignalGenerationResult(null);
      setBacktestRunResult(null);
      await loadDashboard(setDashboardState);
    } catch (error: unknown) {
      setMarketDataFetchResult(null);
      setOperationError({
        operation: "marketDataFetch",
        kind: error instanceof ApiClientError ? error.kind : "unavailable"
      });
    } finally {
      setActiveOperation(null);
      setMarketDataFetchMode(null);
    }
  }

  async function handleSignalGeneration() {
    if (activeOperation) {
      return;
    }

    setActiveOperation("signalGeneration");
    setOperationError(null);

    try {
      const generationResult = await generateStrategySignal();
      setSignalGenerationResult(generationResult);
      setMarketDataFetchResult(null);
      setBacktestRunResult(null);
      await refreshDashboardSignalState(generationResult, setDashboardState);
    } catch (error: unknown) {
      setSignalGenerationResult(null);
      setOperationError({
        operation: "signalGeneration",
        kind: error instanceof ApiClientError ? error.kind : "unavailable"
      });
    } finally {
      setActiveOperation(null);
    }
  }

  async function handleBacktestRun(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (activeOperation) {
      return;
    }

    const validationError = validateBacktestDates(backtestForm);
    if (validationError) {
      setBacktestValidationError(validationError);
      setBacktestRunResult(null);
      return;
    }

    setActiveOperation("backtestRun");
    setBacktestValidationError(null);
    setOperationError(null);

    try {
      const result = await runBacktest(backtestForm.startDate, backtestForm.endDate);
      setBacktestRunResult(result);
      setMarketDataFetchResult(null);
      setSignalGenerationResult(null);
      await loadDashboard(setDashboardState);
    } catch (error: unknown) {
      setBacktestRunResult(null);
      setOperationError({
        operation: "backtestRun",
        kind: error instanceof ApiClientError ? error.kind : "unavailable"
      });
    } finally {
      setActiveOperation(null);
    }
  }

  const data = dashboardState.status === "ready" ? dashboardState.data : undefined;
  const hasActiveOperation = activeOperation !== null;
  const marketFetchAction = {
    isDisabled: hasActiveOperation,
    isLoading: activeOperation === "marketDataFetch",
    onClick: () => {
      void handleMarketDataFetch("incremental");
    }
  };
  const signalGenerationAction = {
    isDisabled: hasActiveOperation,
    isLoading: activeOperation === "signalGeneration",
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
        <FeedbackMessage className="dashboard-alert" variant="error">
          Dashboard API unavailable: {dashboardState.error}
        </FeedbackMessage>
      ) : null}

      {dashboardState.status === "loading" ? (
        <FeedbackMessage variant="loading">Loading dashboard data.</FeedbackMessage>
      ) : null}

      <div className="dashboard-grid" aria-label="Dashboard workflow summary">
        <article className="dashboard-panel market-panel">
          <PanelHeading eyebrow="Market" title="Market data" />
          <div className="metric-row">
            <Metric
              label="Price rows"
              value={data ? `${formatInteger(data.market_data.price_rows)} rows` : "Loading"}
            />
            <Metric
              label="Covered ETFs"
              value={data ? `${formatInteger(data.market_data.covered_etfs)} ETFs` : "Loading"}
            />
          </div>
          {data?.market_data.price_rows === 0 ? (
            <EmptyAction
              actionLabel="Fetch market data"
              className="market-empty-state"
              isDisabled={marketFetchAction.isDisabled}
              isLoading={marketFetchAction.isLoading}
              message="No local market prices are stored yet. Fetch market data to populate dashboard coverage."
              onClick={marketFetchAction.onClick}
            />
          ) : null}
          <dl className="compact-list">
            <Detail label="Earliest trade date" value={formatDate(data?.market_data.earliest_trade_date)} />
            <Detail label="Latest trade date" value={formatDate(data?.market_data.latest_trade_date)} />
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
            <Detail label="Top N" value={data ? formatInteger(data.strategy.selection.top_n) : "Loading"} />
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
            isDisabled={signalGenerationAction.isDisabled}
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
          {activeOperation ? <OperationPendingFeedback activeOperation={activeOperation} mode={marketDataFetchMode} /> : null}
          {operationError ? (
            <FeedbackMessage className="dashboard-alert operation-alert" variant="error">
              {formatOperationError(operationError)}
            </FeedbackMessage>
          ) : null}
          {marketDataFetchResult ? <MarketDataFetchSummary result={marketDataFetchResult} /> : null}
          {signalGenerationResult ? <SignalGenerationSummary result={signalGenerationResult} /> : null}
          {backtestRunResult ? <BacktestRunSummary result={backtestRunResult} /> : null}
          {backtestValidationError ? (
            <FeedbackMessage className="dashboard-alert operation-alert" variant="error">
              {backtestValidationError}
            </FeedbackMessage>
          ) : null}
          <div className="operation-list">
            <button type="button" disabled={marketFetchAction.isDisabled} onClick={marketFetchAction.onClick}>
              {marketDataFetchMode === "incremental" ? "Fetching market data" : "Fetch market data"}
            </button>
            <button
              type="button"
              disabled={marketFetchAction.isDisabled}
              onClick={() => {
                void handleMarketDataFetch("full");
              }}
            >
              {marketDataFetchMode === "full" ? "Running full fetch" : "Full fetch for initialization or repair"}
            </button>
            <button
              type="button"
              disabled={signalGenerationAction.isDisabled}
              onClick={signalGenerationAction.onClick}
            >
              {signalGenerationAction.isLoading ? "Generating signal" : "Generate signal"}
            </button>
          </div>
          <form className="backtest-run-form" onSubmit={(event) => void handleBacktestRun(event)}>
            <label>
              <span>Start date</span>
              <input
                type="text"
                inputMode="numeric"
                placeholder="YYYY-MM-DD"
                value={backtestForm.startDate}
                onChange={(event) => {
                  setBacktestForm((current) => ({
                    ...current,
                    startDate: event.target.value
                  }));
                }}
              />
            </label>
            <label>
              <span>End date</span>
              <input
                type="text"
                inputMode="numeric"
                placeholder="YYYY-MM-DD"
                value={backtestForm.endDate}
                onChange={(event) => {
                  setBacktestForm((current) => ({
                    ...current,
                    endDate: event.target.value
                  }));
                }}
              />
            </label>
            <div className="operation-list">
              <button type="submit" disabled={hasActiveOperation}>
                {activeOperation === "backtestRun" ? "Running backtest" : "Run backtest"}
              </button>
            </div>
          </form>
        </article>
      </div>
    </section>
  );
}

function SignalGenerationSummary({ result }: { result: StrategySignalGenerationResponse }) {
  return (
    <FeedbackMessage
      className={`operation-summary operation-summary-${result.status}`}
      variant={result.status === "success" ? "success" : "error"}
    >
      <strong>Signal generation {result.status}</strong>
      <dl className="compact-list">
        <Detail label="Signal" value={`#${formatInteger(result.signal_id)}`} />
        <Detail label="Signal date" value={formatDate(result.signal_date)} />
        <Detail label="Result" value={formatNullableText(result.result)} />
        <Detail label="Positions" value={formatInteger(result.positions.length)} />
      </dl>
      {result.error_message ? <p className="operation-guidance">{result.error_message}</p> : null}
    </FeedbackMessage>
  );
}

function MarketDataFetchSummary({ result }: { result: MarketDataFetchResponse }) {
  const hasFailures = result.status === "partial" || result.status === "failed";

  return (
    <FeedbackMessage
      className={`operation-summary operation-summary-${result.status}`}
      variant={result.status === "success" ? "success" : "error"}
    >
      <strong>Market data fetch {result.status}</strong>
      <dl className="compact-list">
        <Detail label="Fetched" value={formatRows(result.rows_fetched)} />
        <Detail label="Inserted" value={formatRows(result.rows_inserted)} />
        <Detail label="Updated" value={formatRows(result.rows_updated)} />
        {hasFailures ? (
          <>
            <Detail label="Failed symbols" value={formatFailedSymbols(result.failed_symbols)} />
            <Detail label="Error summary" value={formatNullableText(result.error_message)} />
          </>
        ) : null}
      </dl>
      {hasFailures ? (
        <p className="operation-guidance">
          Retry the fetch after checking the data source availability and local ETF/data state.
        </p>
      ) : null}
    </FeedbackMessage>
  );
}

function BacktestRunSummary({ result }: { result: BacktestRunResponse }) {
  return (
    <FeedbackMessage
      className={`operation-summary operation-summary-${result.status}`}
      variant={result.status === "success" ? "success" : "info"}
    >
      <strong>Backtest run {result.status}</strong>
      <dl className="compact-list">
        <Detail label="Run" value={`#${formatInteger(result.run_id)}`} />
        <Detail label="Status" value={result.status} />
        <Detail label="Trading days" value={formatInteger(result.trading_day_count)} />
        <Detail label="Signals" value={formatInteger(result.signal_count)} />
        <Detail label="Total return" value={formatRatioAsPercent(result.total_return)} />
        <Detail label="Annualized return" value={formatRatioAsPercent(result.annualized_return)} />
        <Detail label="Max drawdown" value={formatRatioAsPercent(result.max_drawdown)} />
        <Detail label="Volatility" value={formatRatioAsPercent(result.volatility)} />
        <Detail label="Sharpe" value={formatNullableText(result.sharpe_ratio)} />
      </dl>
      <a className="operation-link" href={`/backtests/${result.run_id}`}>
        View backtest detail
      </a>
    </FeedbackMessage>
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
          <Detail label="Fetched" value={formatRows(log.rows_fetched)} />
          <Detail label="Inserted" value={formatRows(log.rows_inserted)} />
          <Detail label="Updated" value={formatRows(log.rows_updated)} />
          <Detail label="Error summary" value={formatNullableText(log.error_summary)} />
        </dl>
      ))}
    </div>
  );
}

function SignalSummary({
  isDisabled,
  isGeneratingSignal,
  isLoading,
  onGenerateSignal,
  signal
}: {
  isGeneratingSignal: boolean;
  isDisabled: boolean;
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
        isDisabled={isDisabled}
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
        <Detail label="Signal date" value={formatDate(signal.signal_date)} />
        <Detail label="Status" value={signal.status} />
        <Detail label="Result" value={formatNullableText(signal.result)} />
        <Detail label="Fallback" value={formatBoolean(signal.is_fallback)} />
        <Detail label="Target holdings" value={formatInteger(signal.position_count)} />
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
      <p className="empty-state">
        No local backtest run exists yet. Use the Operations panel to run a backtest.
      </p>
    );
  }

  return (
    <>
      <strong className="panel-primary">Backtest #{backtest.run_id}</strong>
      <dl className="compact-list">
        <Detail label="Range" value={`${formatDate(backtest.start_date)} to ${formatDate(backtest.end_date)}`} />
        <Detail label="Status" value={backtest.status} />
        <Detail label="Total return" value={formatRatioAsPercent(backtest.total_return)} />
        <Detail label="Max drawdown" value={formatRatioAsPercent(backtest.max_drawdown)} />
        <Detail label="Sharpe" value={formatNullableText(backtest.sharpe_ratio)} />
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
  isDisabled = false,
  loadingLabel,
  message,
  onClick
}: {
  actionLabel: string;
  className?: string;
  isLoading?: boolean;
  isDisabled?: boolean;
  loadingLabel?: string;
  message: string;
  onClick?: () => void;
}) {
  return (
    <div className={className}>
      <p className="empty-state">{message}</p>
      <div className="operation-list empty-action">
        <button type="button" disabled={isDisabled || isLoading || !onClick} onClick={onClick}>
          {isLoading ? (loadingLabel ?? actionLabel) : actionLabel}
        </button>
      </div>
    </div>
  );
}

function OperationPendingFeedback({
  activeOperation,
  mode
}: {
  activeOperation: ActiveOperation;
  mode: MarketDataFetchMode | null;
}) {
  return <FeedbackMessage variant="loading">{getOperationPendingMessage(activeOperation, mode)}</FeedbackMessage>;
}

function getOperationPendingMessage(
  activeOperation: ActiveOperation,
  mode: MarketDataFetchMode | null
): string {
  if (activeOperation === "marketDataFetch") {
    return mode === "full" ? "Running full market data fetch." : "Fetching market data.";
  }

  if (activeOperation === "signalGeneration") {
    return "Generating latest strategy signal.";
  }

  return "Running backtest.";
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

function formatMomentumWindows(momentum: DashboardResponse["strategy"]["momentum"]): string {
  return `${formatInteger(momentum.short_window_days)} / ${formatInteger(momentum.long_window_days)} days`;
}

function formatScoreWeights(scoreWeights: DashboardResponse["strategy"]["score_weights"]): string {
  return `Short ${formatCompactNumber(scoreWeights.short)} / Long ${formatCompactNumber(scoreWeights.long)}`;
}

function formatDefensiveAsset(asset: DashboardResponse["strategy"]["defense"]["asset"]): string {
  return `${asset.exchange}:${asset.symbol}`;
}

function formatFailedSymbols(symbols: string[]): string {
  return symbols.length > 0 ? symbols.join(", ") : formatNullableText(null);
}

function formatOperationError(error: OperationError): string {
  const operationLabel = getOperationLabel(error.operation);
  return `${operationLabel} failed: ${error.kind}`;
}

function getOperationLabel(operation: OperationError["operation"]): string {
  if (operation === "signalGeneration") {
    return "Signal generation";
  }

  if (operation === "backtestRun") {
    return "Backtest run";
  }

  return "Market data fetch";
}

function validateBacktestDates(form: BacktestFormState): string | null {
  const startDate = parseIsoDate(form.startDate);
  const endDate = parseIsoDate(form.endDate);

  if (!startDate || !endDate) {
    return "Enter dates in YYYY-MM-DD format.";
  }

  if (startDate.getTime() > endDate.getTime()) {
    return "Start date must be on or before end date.";
  }

  return null;
}

function parseIsoDate(value: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return null;
  }

  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));

  if (
    parsed.getUTCFullYear() !== year ||
    parsed.getUTCMonth() !== month - 1 ||
    parsed.getUTCDate() !== day
  ) {
    return null;
  }

  return parsed;
}
