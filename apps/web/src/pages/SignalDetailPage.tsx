import { useEffect, useState } from "react";
import {
  ApiClientError,
  type LatestStrategySignalPosition,
  type LatestStrategySignalResponse,
  getLatestStrategySignal
} from "../api/client";

type SignalDetailPageProps = {
  signalId: string;
};

type SignalDetailState =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: LatestStrategySignalResponse; error?: never }
  | { status: "error"; data?: never; error: string };

export function SignalDetailPage({ signalId }: SignalDetailPageProps) {
  const [signalState, setSignalState] = useState<SignalDetailState>({
    status: "loading"
  });

  useEffect(() => {
    let isCurrent = true;

    getLatestStrategySignal()
      .then((data) => {
        if (isCurrent) {
          setSignalState({ status: "ready", data });
        }
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setSignalState({
            status: "error",
            error: error instanceof ApiClientError ? error.kind : "unavailable"
          });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [signalId]);

  return (
    <section className="page detail-page">
      <div className="page-heading">
        <p>Signal research workspace</p>
        <h2>Signal Detail</h2>
      </div>
      {renderSignalDetail(signalState)}
    </section>
  );
}

function renderSignalDetail(signalState: SignalDetailState) {
  if (signalState.status === "loading") {
    return <p className="empty-state">Loading latest signal.</p>;
  }

  if (signalState.status === "error") {
    return <p className="dashboard-alert">Latest signal API unavailable: {signalState.error}</p>;
  }

  if (!signalState.data.has_signal || signalState.data.signal === null) {
    return (
      <p className="empty-state">
        No successful local signal exists yet. Generate a signal from the Dashboard after market data is ready.
      </p>
    );
  }

  const signal = signalState.data.signal;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Signal #{signal.signal_id}</strong>
      <dl className="compact-list">
        <Detail label="Signal date" value={signal.signal_date} />
        <Detail label="Config version" value={signal.config_version} />
        <Detail label="Result" value={formatOptional(signal.result)} />
        <Detail label="Fallback" value={signal.is_fallback ? "Yes" : "No"} />
        <Detail label="Generated at" value={signal.generated_at} />
      </dl>
      <section className="holdings-section" aria-labelledby="target-holdings-heading">
        <h3 id="target-holdings-heading">Target holdings</h3>
        {renderTargetHoldings(signalState.data.positions)}
      </section>
    </article>
  );
}

function renderTargetHoldings(positions: LatestStrategySignalPosition[]) {
  if (positions.length === 0) {
    return <p className="empty-state">No target holdings were stored for this signal.</p>;
  }

  return (
    <div className="holdings-table-wrap">
      <table className="holdings-table">
        <thead>
          <tr>
            <th scope="col">Exchange</th>
            <th scope="col">Symbol</th>
            <th scope="col">Target weight</th>
            <th scope="col">Rank</th>
            <th scope="col">Score</th>
            <th scope="col">Fallback</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => (
            <tr key={`${position.exchange}:${position.symbol}`}>
              <td>{position.exchange}</td>
              <td>{position.symbol}</td>
              <td>{formatTargetWeight(position.target_weight)}</td>
              <td>{formatNullableNumber(position.rank)}</td>
              <td>{formatNullableDecimal(position.score)}</td>
              <td>{formatFallback(position.is_fallback)}</td>
            </tr>
          ))}
        </tbody>
      </table>
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

function formatOptional(value: string | null): string {
  return value ?? "None";
}

function formatTargetWeight(value: string): string {
  const percentage = Number(value) * 100;

  if (!Number.isFinite(percentage)) {
    return value;
  }

  return `${trimFixed(percentage, 4)}%`;
}

function formatNullableNumber(value: number | null): string {
  return value === null ? "None" : String(value);
}

function formatNullableDecimal(value: string | null): string {
  if (value === null) {
    return "None";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return value;
  }

  return trimFixed(numericValue, 6);
}

function formatFallback(value: boolean): string {
  return value ? "Yes" : "No";
}

function trimFixed(value: number, digits: number): string {
  return value
    .toFixed(digits)
    .replace(/(\.\d*?)0+$/, "$1")
    .replace(/\.$/, "");
}
