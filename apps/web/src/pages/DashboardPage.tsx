import { useEffect, useState } from "react";
import {
  ApiClientError,
  type DashboardBacktestSummary,
  type DashboardResponse,
  type DashboardSignalSummary,
  getDashboard
} from "../api/client";

type DashboardState =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: DashboardResponse; error?: never }
  | { status: "error"; data?: never; error: string };

export function DashboardPage() {
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    status: "loading"
  });

  useEffect(() => {
    let isCurrent = true;

    getDashboard()
      .then((dashboard) => {
        if (isCurrent) {
          setDashboardState({ status: "ready", data: dashboard });
        }
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setDashboardState({
            status: "error",
            error: error instanceof ApiClientError ? error.kind : "unavailable"
          });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  const data = dashboardState.status === "ready" ? dashboardState.data : undefined;

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
            <p className="empty-state market-empty-state">No local market data has been stored yet.</p>
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
          <SignalSummary signal={data?.latest_signal} isLoading={dashboardState.status === "loading"} />
        </article>

        <article className="dashboard-panel backtest-panel">
          <PanelHeading eyebrow="Backtest" title="Recent backtest" />
          <BacktestSummary
            backtest={data?.recent_backtest}
            isLoading={dashboardState.status === "loading"}
          />
        </article>

        <article className="dashboard-panel operations-panel">
          <PanelHeading eyebrow="Actions" title="Operations" />
          <div className="operation-list">
            <button type="button" disabled>
              Fetch market data
            </button>
            <button type="button" disabled>
              Generate signal
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

function SignalSummary({
  isLoading,
  signal
}: {
  isLoading: boolean;
  signal: DashboardSignalSummary | null | undefined;
}) {
  if (isLoading) {
    return <p className="empty-state">Loading latest signal.</p>;
  }

  if (!signal) {
    return (
      <>
        <p className="empty-state">No successful signal has been generated yet.</p>
        <div className="operation-list signal-empty-action">
          <button type="button" disabled>
            Generate signal
          </button>
        </div>
      </>
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
    return <p className="empty-state">No backtest run has been recorded yet.</p>;
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

function formatBoolean(value: boolean): string {
  return value ? "Yes" : "No";
}

function formatPercent(value: string | null): string {
  if (value === null) {
    return "Not available";
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(2)}%` : value;
}
