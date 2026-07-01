import { useEffect, useState } from "react";
import {
  ApiClientError,
  type BacktestDetailResponse,
  getBacktestDetail
} from "../api/client";

type BacktestDetailPageProps = {
  backtestId: string;
};

type BacktestDetailState =
  | { status: "loading"; backtestId: string; data?: never; error?: never }
  | { status: "ready"; backtestId: string; data: BacktestDetailResponse; error?: never }
  | { status: "not-found"; backtestId: string; data?: never; error?: never }
  | { status: "error"; backtestId: string; data?: never; error: string };

export function BacktestDetailPage({ backtestId }: BacktestDetailPageProps) {
  const [backtestState, setBacktestState] = useState<BacktestDetailState>({
    status: "loading",
    backtestId
  });

  useEffect(() => {
    let isCurrent = true;

    getBacktestDetail(backtestId)
      .then((data) => {
        if (isCurrent) {
          setBacktestState({ status: "ready", backtestId, data });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (error instanceof ApiClientError && error.status === 404) {
          setBacktestState({ status: "not-found", backtestId });
          return;
        }

        setBacktestState({
          status: "error",
          backtestId,
          error: error instanceof ApiClientError ? error.kind : "unavailable"
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [backtestId]);

  return (
    <section className="page detail-page">
      <div className="page-heading">
        <p>Backtest research workspace</p>
        <h2>Backtest Detail</h2>
      </div>
      {renderBacktestDetail(getCurrentBacktestState(backtestState, backtestId), backtestId)}
    </section>
  );
}

function getCurrentBacktestState(
  backtestState: BacktestDetailState,
  backtestId: string
): BacktestDetailState {
  if (backtestState.backtestId === backtestId) {
    return backtestState;
  }

  return { status: "loading", backtestId };
}

function renderBacktestDetail(backtestState: BacktestDetailState, backtestId: string) {
  if (backtestState.status === "loading") {
    return <p className="empty-state">Loading backtest detail.</p>;
  }

  if (backtestState.status === "not-found") {
    return <p className="empty-state">Backtest run {backtestId} was not found.</p>;
  }

  if (backtestState.status === "error") {
    return <p className="dashboard-alert">Backtest detail API unavailable: {backtestState.error}</p>;
  }

  const { metrics, run } = backtestState.data;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Backtest #{run.run_id}</strong>
      <dl className="compact-list">
        <Detail label="Strategy" value={run.strategy_name} />
        <Detail label="Config version" value={run.config_version} />
        <Detail label="Date range" value={`${run.start_date} to ${run.end_date}`} />
        <Detail label="Status" value={run.status} />
        <Detail label="Started at" value={run.started_at} />
        <Detail label="Finished at" value={formatOptional(run.finished_at)} />
        <Detail label="Error message" value={formatOptional(run.error_message)} />
      </dl>
      <section className="holdings-section" aria-labelledby="backtest-metrics-heading">
        <h3 id="backtest-metrics-heading">Metrics</h3>
        <dl className="compact-list">
          <Detail label="Total return" value={formatPercent(metrics.total_return)} />
          <Detail label="Annualized return" value={formatPercent(metrics.annualized_return)} />
          <Detail label="Max drawdown" value={formatPercent(metrics.max_drawdown)} />
          <Detail label="Volatility" value={formatPercent(metrics.volatility)} />
          <Detail label="Sharpe" value={formatOptional(metrics.sharpe_ratio)} />
        </dl>
      </section>
      <section className="holdings-section" aria-labelledby="backtest-parameters-heading">
        <h3 id="backtest-parameters-heading">Parameters</h3>
        <pre className="parameter-summary">{formatParameterSummary(run.parameters_json)}</pre>
      </section>
    </article>
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

function formatOptional(value: string | null | undefined): string {
  return value ?? "Not available";
}

function formatPercent(value: string | null): string {
  if (value === null) {
    return "Not available";
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(2)}%` : value;
}

function formatParameterSummary(value: string | null): string {
  if (!value) {
    return "Not available";
  }

  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}
