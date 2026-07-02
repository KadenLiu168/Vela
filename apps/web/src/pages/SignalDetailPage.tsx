import { useEffect, useState } from "react";
import {
  ApiClientError,
  type LatestStrategySignalPosition,
  type LatestStrategySignalResponse,
  getLatestStrategySignal
} from "../api/client";
import { FeedbackMessage } from "../components/FeedbackMessage";
import {
  formatBoolean,
  formatDate,
  formatDecimal,
  formatNullableInteger,
  formatNullableText,
  formatTargetWeight,
  formatTimestamp
} from "../utils/formatters";

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
    return <FeedbackMessage variant="loading">Loading latest signal.</FeedbackMessage>;
  }

  if (signalState.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Latest signal API unavailable: {signalState.error}
      </FeedbackMessage>
    );
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
        <Detail label="Signal date" value={formatDate(signal.signal_date)} />
        <Detail label="Config version" value={signal.config_version} />
        <Detail label="Result" value={formatNullableText(signal.result)} />
        <Detail label="Fallback" value={formatBoolean(signal.is_fallback)} />
        <Detail label="Generated at" value={formatTimestamp(signal.generated_at)} />
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
              <td>{formatNullableInteger(position.rank)}</td>
              <td>{formatDecimal(position.score, 6)}</td>
              <td>{formatBoolean(position.is_fallback)}</td>
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
