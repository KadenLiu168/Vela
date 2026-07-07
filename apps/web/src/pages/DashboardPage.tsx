import { useEffect, useState } from "react";
import {
  ApiClientError,
  type ApiErrorCategory,
  type BacktestRunResponse,
  type BootstrapResponse,
  type DashboardBacktestSummary,
  type DashboardFetchLogSummary,
  type DashboardResponse,
  type DashboardSignalSummary,
  type LatestStrategySignalResponse,
  type MarketDataFetchResponse,
  type StrategySignalGenerationResponse,
  bootstrapLocalDatabase,
  fetchFullMarketData,
  fetchIncrementalMarketData,
  generateStrategySignal,
  getDashboard,
  getLatestStrategySignal,
  runBacktest
} from "../api/client";
import { EmptyState, FeedbackMessage } from "../components";
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
type ActiveOperation = "backtestRun" | "bootstrap" | "marketDataFetch" | "signalGeneration";
type OperationError =
  | { operation: "bootstrap"; category: ApiErrorCategory; message: string; status: number | null }
  | { operation: "marketDataFetch"; category: ApiErrorCategory; message: string; status: number | null }
  | { operation: "signalGeneration"; category: ApiErrorCategory; message: string; status: number | null }
  | { operation: "backtestRun"; category: ApiErrorCategory; message: string; status: number | null };

type BacktestFormState = {
  startDate: string;
  endDate: string;
};

type DashboardPageProps = {
  backtestForm?: BacktestFormState;
  onBacktestFormChange?: (form: BacktestFormState) => void;
};

export function DashboardPage({
  backtestForm: externalBacktestForm,
  onBacktestFormChange
}: DashboardPageProps = {}) {
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
  const [internalForm, setInternalForm] = useState<BacktestFormState>({
    startDate: "",
    endDate: ""
  });
  const backtestForm = externalBacktestForm ?? internalForm;
  const updateBacktestForm = onBacktestFormChange ?? setInternalForm;
  const [backtestValidationError, setBacktestValidationError] = useState<string | null>(null);
  const [bootstrapResult, setBootstrapResult] = useState<BootstrapResponse | null>(null);

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
      setOperationError(createOperationError("marketDataFetch", error));
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
      setOperationError(createOperationError("signalGeneration", error));
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
      setOperationError(createOperationError("backtestRun", error));
    } finally {
      setActiveOperation(null);
    }
  }

  async function handleBootstrap() {
    if (activeOperation) {
      return;
    }

    setActiveOperation("bootstrap");
    setOperationError(null);
    setBootstrapResult(null);
    setMarketDataFetchResult(null);
    setSignalGenerationResult(null);
    setBacktestRunResult(null);

    try {
      const result = await bootstrapLocalDatabase();
      setBootstrapResult(result);
      await loadDashboard(setDashboardState);
    } catch (error: unknown) {
      setOperationError(createOperationError("bootstrap", error));
    } finally {
      setActiveOperation(null);
    }
  }

  function handleDashboardRefresh() {
    if (activeOperation) {
      return;
    }

    setDashboardState({ status: "loading" });
    void loadDashboard(setDashboardState);
  }

  const data = dashboardState.status === "ready" ? dashboardState.data : undefined;
  const firstRunGuidance = getFirstRunGuidance(dashboardState);
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

  const signalStatusPill = deriveSignalStatusPill(dashboardState, data);
  const backtestStatusPill = deriveBacktestStatusPill(dashboardState, data);
  const fetchStatusPill = deriveFetchStatusPill(dashboardState, data);

  const barColor = (category: string | null | undefined): string => {
    if (category == null) return "var(--color-fog)";
    if (category.startsWith("equity_cn") || category.startsWith("bond")) return "var(--color-coral-red)";
    if (category.startsWith("equity_us")) return "var(--color-iris-violet)";
    if (category.startsWith("equity_hk")) return "var(--color-signal-teal)";
    return "var(--color-fog)";
  };

  return (
    <section className="page dashboard-page">
      <div className="page-heading dashboard-heading">
        <div>
          <p>Local research workflow</p>
          <h1>Dashboard</h1>
        </div>
        <div className="dashboard-heading-actions">
          <span className={`status-surface dashboard-load-state dashboard-load-state-${dashboardState.status}`}>
            {getLoadLabel(dashboardState)}
          </span>
          <button
            className="dashboard-refresh-action button-secondary"
            type="button"
            disabled={hasActiveOperation || dashboardState.status === "loading"}
            onClick={handleDashboardRefresh}
          >
            Refresh Dashboard
          </button>
        </div>
      </div>

      {dashboardState.status === "error" ? (
        <FeedbackMessage className="dashboard-alert" variant="error">
          Dashboard API unavailable: {dashboardState.error}
        </FeedbackMessage>
      ) : null}

      {dashboardState.status === "loading" ? (
        <FeedbackMessage variant="loading">Loading dashboard data.</FeedbackMessage>
      ) : null}

      {firstRunGuidance ? <FirstRunGuidance message={firstRunGuidance} /> : null}

      <div className="dashboard-grid" aria-label="Dashboard workflow summary">
        <article className="dashboard-panel market-panel">
          <PanelHeading eyebrow="Price" title="Market data" />
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
          {data?.market_data.earliest_trade_date && data?.market_data.latest_trade_date ? (
            <div className="coverage-timeline">
              <span className="coverage-timeline-end">
                <span className="coverage-timeline-label">Earliest</span>
                <time className="coverage-timeline-date">{formatDate(data.market_data.earliest_trade_date)}</time>
              </span>
              <div className="coverage-timeline-bar" />
              <span className="coverage-timeline-end">
                <span className="coverage-timeline-label">Latest</span>
                <time className="coverage-timeline-date">{formatDate(data.market_data.latest_trade_date)}</time>
              </span>
            </div>
          ) : null}
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
          {data?.market_data.etf_list != null && data.market_data.etf_list.length > 0 ? (
            <div className="etf-row-list">
              {data.market_data.etf_list.map((etf) => (
                <div className="etf-row" key={`${etf.exchange}:${etf.symbol}`}>
                  <span className="etf-row-bar" style={{ backgroundColor: barColor(etf.category) }} />
                  <span className="etf-row-symbol">{etf.symbol}</span>
                  <span className="etf-row-dot">·</span>
                  <span className="etf-row-name">{etf.name}</span>
                  <span className="etf-row-date">{etf.earliest_trade_date ? formatDate(etf.earliest_trade_date) : "—"}</span>
                </div>
              ))}
            </div>
          ) : null}
        </article>

        <article className="dashboard-panel strategy-panel">
          <PanelHeading eyebrow="Config" title="Strategy" />
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
            <Detail
              label="Rebalance frequency"
              value={data ? data.strategy.rebalance.frequency : "Loading"}
            />
          </dl>
        </article>

        <article className="dashboard-panel operations-panel">
          <PanelHeading eyebrow="Actions" title="Operations" />
          {activeOperation ? <OperationPendingFeedback activeOperation={activeOperation} mode={marketDataFetchMode} /> : null}
          {operationError ? (
            <FeedbackMessage className="dashboard-alert operation-alert" variant="error">
              <OperationErrorSummary error={operationError} />
            </FeedbackMessage>
          ) : null}
          {bootstrapResult ? <BootstrapSummary result={bootstrapResult} /> : null}
          {marketDataFetchResult ? <MarketDataFetchSummary result={marketDataFetchResult} /> : null}
          {signalGenerationResult ? <SignalGenerationSummary result={signalGenerationResult} /> : null}
          {backtestRunResult ? <BacktestRunSummary result={backtestRunResult} /> : null}
          {backtestValidationError ? (
            <FeedbackMessage className="dashboard-alert operation-alert" variant="error">
              {backtestValidationError}
            </FeedbackMessage>
          ) : null}
          <div className="operation-list">
            <button
              className="button-secondary"
              type="button"
              disabled={marketFetchAction.isDisabled}
              onClick={marketFetchAction.onClick}
            >
              {marketDataFetchMode === "incremental" ? "Fetching market data" : "Fetch market data"}
            </button>
            <button
              className="button-secondary"
              type="button"
              disabled={signalGenerationAction.isDisabled}
              onClick={signalGenerationAction.onClick}
            >
              {signalGenerationAction.isLoading ? "Generating signal" : "Generate signal"}
            </button>
            <button
              className="bootstrap-action button-primary"
              type="button"
              disabled={hasActiveOperation}
              onClick={() => {
                void handleBootstrap();
              }}
            >
              {activeOperation === "bootstrap" ? "Running bootstrap" : "Bootstrap / Setup database & data"}
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
                  updateBacktestForm({
                    ...backtestForm,
                    startDate: event.target.value
                  });
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
                  updateBacktestForm({
                    ...backtestForm,
                    endDate: event.target.value
                  });
                }}
              />
            </label>
            <div className="operation-list">
              <button
                className="button-secondary"
                type="submit"
                disabled={hasActiveOperation}
              >
                {activeOperation === "backtestRun" ? "Running backtest" : "Run backtest"}
              </button>
            </div>
          </form>
        </article>

        <article className="dashboard-panel signal-panel" data-testid="workflow-panel-signal">
          <PanelHeading title="Latest signal" statusPill={signalStatusPill} />
          <SignalSummary
            signal={data?.latest_signal}
            isDisabled={signalGenerationAction.isDisabled}
            isGeneratingSignal={signalGenerationAction.isLoading}
            isLoading={dashboardState.status === "loading"}
            onGenerateSignal={signalGenerationAction.onClick}
          />
        </article>

        <article className="dashboard-panel backtest-panel" data-testid="workflow-panel-backtest">
          <PanelHeading title="Latest backtest" statusPill={backtestStatusPill} />
          <BacktestSummary
            backtest={data?.recent_backtest}
            isLoading={dashboardState.status === "loading"}
          />
        </article>

        <article className="dashboard-panel fetch-log-panel" data-testid="workflow-panel-fetches">
          <PanelHeading title="Data fetches" statusPill={fetchStatusPill} />
          <FetchLogSummary logs={data?.recent_fetch_logs} isLoading={dashboardState.status === "loading"} />
        </article>
      </div>
    </section>
  );
}

function FirstRunGuidance({ message }: { message: string }) {
  return (
    <section className="first-run-guidance" aria-labelledby="first-run-guidance-title">
      <div>
        <span>Local setup</span>
        <h3 id="first-run-guidance-title">First run setup</h3>
      </div>
      <p>{message}</p>
    </section>
  );
}

function BootstrapSummary({ result }: { result: BootstrapResponse }) {
  return (
    <FeedbackMessage
      className={`operation-summary operation-summary-${result.status}`}
      variant={result.status === "success" ? "success" : "error"}
    >
      <strong>Bootstrap {result.status}</strong>
      <dl className="compact-list">
        {result.steps.map((step) => (
          <BootstrapStepRow key={step.name} step={step} />
        ))}
      </dl>
      <p className="operation-guidance">
        Total duration: {result.total_duration_seconds.toFixed(1)}s
      </p>
      {result.status === "failed" ? (
        <p className="operation-guidance">
          Fix the reported issue in {result.failed_step} and re-run the bootstrap action.
        </p>
      ) : null}
    </FeedbackMessage>
  );
}

function BootstrapStepRow({ step }: { step: { name: string; status: string; error_message: string | null } }) {
  const stepLabel =
    step.name === "migrate"
      ? "Migrate"
      : step.name === "sync_etf_pool"
        ? "Sync ETF pool"
        : "Fetch full market data";
  const statusIcon = step.status === "success" ? "✓" : "✗";
  const statusClass = step.status === "success" ? "bootstrap-step-success" : "bootstrap-step-failed";

  return (
    <>
      <dt className={statusClass}>
        {statusIcon} {stepLabel}
      </dt>
      <dd>{step.error_message ? formatNullableText(step.error_message) : step.status}</dd>
    </>
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
    return <EmptyState>Loading fetch history.</EmptyState>;
  }

  if (!logs || logs.length === 0) {
    return <EmptyState>No market data fetch history exists yet.</EmptyState>;
  }

  return (
    <div className="fetch-log-list">
      {logs.map((log) => (
        <div className="fetch-log-entry" key={log.fetch_log_id}>
          <div className="fetch-log-entry__head">
            <time className="fetch-log-entry__time" dateTime={log.fetch_time}>
              {log.fetch_time}
            </time>
            <StatusPillBadge {...deriveFetchEntryPill(log.status)} />
          </div>
          <div className="fetch-log-entry__meta">
            {`Fetched ${formatRows(log.rows_fetched)} · Inserted ${formatRows(
              log.rows_inserted
            )} · Updated ${formatRows(log.rows_updated)}`}
          </div>
          {log.error_summary ? (
            <details className="fetch-log-entry__error">
              <summary>Show error</summary>
              <p className="fetch-log-entry__error-body">{log.error_summary}</p>
            </details>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function deriveFetchEntryPill(status: string): StatusPill {
  if (status === "success") {
    return { label: "Active", variant: "success" };
  }

  if (status === "partial") {
    return { label: "Partial", variant: "partial" };
  }

  if (status === "failed") {
    return { label: "Errors", variant: "error" };
  }

  return { label: status || "Unknown", variant: "neutral" };
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
    return <EmptyState>Loading latest signal.</EmptyState>;
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
      <a className="operation-link" href={`/signals/${signal.signal_id}`}>
        View signal detail
      </a>
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
    return <EmptyState>Loading recent backtest.</EmptyState>;
  }

  if (!backtest) {
    return (
      <EmptyState>
        No local backtest run exists yet. Enter a date range in Operations, then run a backtest.
      </EmptyState>
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
      <a className="operation-link" href={`/backtests/${backtest.run_id}`}>
        View backtest detail
      </a>
    </>
  );
}

function deriveSignalStatusPill(
  state: DashboardState,
  data: DashboardResponse | undefined
): StatusPill {
  if (state.status === "loading") {
    return { label: "Loading", variant: "loading" };
  }

  const signal = data?.latest_signal ?? null;
  if (!signal) {
    return { label: "No data", variant: "neutral" };
  }

  if (signal.status === "success") {
    return { label: "Active", variant: "success" };
  }

  if (signal.status === "partial") {
    return { label: "Partial", variant: "partial" };
  }

  if (signal.status === "failed") {
    return { label: "Errors", variant: "error" };
  }

  return { label: "No data", variant: "neutral" };
}

function deriveBacktestStatusPill(
  state: DashboardState,
  data: DashboardResponse | undefined
): StatusPill {
  if (state.status === "loading") {
    return { label: "Loading", variant: "loading" };
  }

  const backtest = data?.recent_backtest ?? null;
  if (!backtest) {
    return { label: "No data", variant: "neutral" };
  }

  if (backtest.status === "success") {
    return { label: "Active", variant: "success" };
  }

  if (backtest.status === "partial") {
    return { label: "Partial", variant: "partial" };
  }

  if (backtest.status === "failed") {
    return { label: "Errors", variant: "error" };
  }

  return { label: "No data", variant: "neutral" };
}

function deriveFetchStatusPill(
  state: DashboardState,
  data: DashboardResponse | undefined
): StatusPill {
  if (state.status === "loading") {
    return { label: "Loading", variant: "loading" };
  }

  const logs = data?.recent_fetch_logs ?? [];
  if (logs.length === 0) {
    return { label: "No data", variant: "neutral" };
  }

  const latestStatus = logs[0]?.status;
  if (latestStatus === "success") {
    return { label: "Active", variant: "success" };
  }

  if (latestStatus === "partial") {
    return { label: "Partial", variant: "partial" };
  }

  if (latestStatus === "failed") {
    return { label: "Errors", variant: "error" };
  }

  return { label: "No data", variant: "neutral" };
}

type StatusPillVariant = "success" | "partial" | "error" | "neutral" | "loading";

type StatusPill = {
  label: string;
  variant: StatusPillVariant;
};

function StatusPillBadge({ label, variant }: StatusPill) {
  return (
    <span className={`status-pill status-pill-${variant}`} aria-label={`Status: ${label}`}>
      {label}
    </span>
  );
}

function PanelHeading({ eyebrow, title, statusPill }: { eyebrow?: string; title: string; statusPill?: StatusPill }) {
  return (
    <div className="panel-heading">
      <h3>{title}</h3>
      {eyebrow || statusPill ? (
        <div className="panel-heading-end">
          {statusPill ? <StatusPillBadge {...statusPill} /> : null}
          {eyebrow ? <span>{eyebrow}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

function getFirstRunGuidance(state: DashboardState): string | null {
  if (state.status === "error") {
    return "Run vela init-db to initialize the local database, then fetch market data.";
  }

  if (state.status === "ready" && state.data.market_data.price_rows === 0) {
    return "No local market data is available yet. Fetch market data to start using the dashboard.";
  }

  return null;
}

type EmptyActionVariant = "button-primary" | "button-secondary" | "button-tertiary";

function EmptyAction({
  actionLabel,
  className,
  isLoading = false,
  isDisabled = false,
  loadingLabel,
  message,
  onClick,
  variant = "button-secondary"
}: {
  actionLabel: string;
  className?: string;
  isLoading?: boolean;
  isDisabled?: boolean;
  loadingLabel?: string;
  message: string;
  onClick?: () => void;
  variant?: EmptyActionVariant;
}) {
  return (
    <div className={className}>
      <EmptyState>{message}</EmptyState>
      <div className="operation-list empty-action">
        <button
          className={variant}
          type="button"
          disabled={isDisabled || isLoading || !onClick}
          onClick={onClick}
        >
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

function OperationErrorSummary({ error }: { error: OperationError }) {
  return (
    <>
      <strong>{getOperationLabel(error.operation)} failed</strong>
      <dl className="compact-list">
        <Detail label="Type" value={formatOperationErrorCategory(error.category)} />
        <Detail label="Reason" value={formatOperationErrorReason(error)} />
        <Detail label="Next step" value={getOperationErrorGuidance(error.operation)} />
      </dl>
    </>
  );
}

function getOperationPendingMessage(
  activeOperation: ActiveOperation,
  mode: MarketDataFetchMode | null
): string {
  if (activeOperation === "bootstrap") {
    return "Running local setup bootstrap.";
  }

  if (activeOperation === "marketDataFetch") {
    return mode === "full" ? "Running full market data fetch." : "Fetching market data.";
  }

  if (activeOperation === "signalGeneration") {
    return "Generating latest strategy signal.";
  }

  return "Running backtest.";
}

function createOperationError(operation: OperationError["operation"], error: unknown): OperationError {
  if (error instanceof ApiClientError) {
    return {
      operation,
      category: error.category,
      message: error.message,
      status: error.status ?? null
    };
  }

  return {
    operation,
    category: "unexpected",
    message: "Operation request failed",
    status: null
  };
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

function formatOperationErrorReason(error: OperationError): string {
  return error.message || error.category;
}

function formatOperationErrorCategory(category: ApiErrorCategory): string {
  if (category === "not_found") {
    return "Not found";
  }

  if (category === "operation_failed") {
    return "Operation failed";
  }

  if (category === "validation") {
    return "Validation";
  }

  if (category === "network") {
    return "Network";
  }

  return "Unexpected";
}

function getOperationLabel(operation: OperationError["operation"]): string {
  if (operation === "bootstrap") {
    return "Bootstrap";
  }

  if (operation === "signalGeneration") {
    return "Signal generation";
  }

  if (operation === "backtestRun") {
    return "Backtest run";
  }

  return "Market data fetch";
}

function getOperationErrorGuidance(operation: OperationError["operation"]): string {
  if (operation === "bootstrap") {
    return "Verify local strategy configuration and database state before retrying.";
  }

  if (operation === "signalGeneration") {
    return "Fetch market data or review local strategy configuration before retrying.";
  }

  if (operation === "backtestRun") {
    return "Verify the date range and available local market data or signals before retrying.";
  }

  return "Retry after checking data source availability and local ETF/data state.";
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
