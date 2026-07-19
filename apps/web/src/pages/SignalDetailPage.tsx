import { useEffect, useState } from "react";
import {
  ApiClientError,
  type StrategySignalDetailPosition,
  type StrategySignalDetailResponse,
  getStrategySignalDetail
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage } from "../components";
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
  | { status: "loading"; data?: never; error?: never; signalId?: never }
  | { status: "ready"; data: StrategySignalDetailResponse; error?: never; signalId: string }
  | { status: "not-found"; data?: never; error?: never; signalId: string }
  | { status: "error"; data?: never; error: string; signalId: string };

export function SignalDetailPage({ signalId }: SignalDetailPageProps) {
  const [signalState, setSignalState] = useState<SignalDetailState>({
    status: "loading"
  });

  useEffect(() => {
    let isCurrent = true;

    getStrategySignalDetail(signalId)
      .then((data) => {
        if (isCurrent) {
          setSignalState({ status: "ready", data, signalId });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (error instanceof ApiClientError && error.status === 404) {
          setSignalState({ status: "not-found", signalId });
          return;
        }

        setSignalState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          signalId
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [signalId]);

  return (
    <section className="page detail-page signal-detail-page">
      <div className="page-heading">
        <p>Signal research workspace</p>
        <h1>Signal Detail</h1>
      </div>
      {renderSignalDetail(getSignalDetailState(signalState, signalId), signalId)}
    </section>
  );
}

function getSignalDetailState(state: SignalDetailState, signalId: string): SignalDetailState {
  return state.status === "loading" || state.signalId === signalId ? state : { status: "loading" };
}

function renderSignalDetail(signalState: SignalDetailState, signalId: string) {
  if (signalState.status === "loading") {
    return <FeedbackMessage variant="loading">Loading signal detail.</FeedbackMessage>;
  }

  if (signalState.status === "not-found") {
    return <EmptyState>Signal {signalId} was not found.</EmptyState>;
  }

  if (signalState.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Signal detail API unavailable: {signalState.error}
      </FeedbackMessage>
    );
  }

  const signal = signalState.data.signal;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Signal #{signal.signal_id}</strong>
      <dl className="compact-list">
        <DescriptionItem label="Signal date" value={formatDate(signal.signal_date)} />
        <DescriptionItem label="Strategy" value={signal.strategy_id} />
        <DescriptionItem label="Config version" value={signal.config_version} />
        <DescriptionItem label="Result" value={formatNullableText(signal.result)} />
        <DescriptionItem label="Source" value={signal.source} />
        {signal.source === "backtest" && signal.backtest_run_id !== null ? (
          <DescriptionItem
            label="Backtest"
            value={
              <a className="operation-link" href={`/backtests/${signal.backtest_run_id}`}>
                Backtest #{signal.backtest_run_id}
              </a>
            }
          />
        ) : null}
        <DescriptionItem label="Fallback" value={formatBoolean(signal.is_fallback)} />
        <DescriptionItem label="Generated at" value={formatTimestamp(signal.generated_at)} />
      </dl>
      <section className="holdings-section" aria-labelledby="target-holdings-heading">
        <h3 id="target-holdings-heading">Target holdings</h3>
        {renderTargetHoldings(signalState.data.positions)}
      </section>
    </article>
  );
}

function renderTargetHoldings(positions: StrategySignalDetailPosition[]) {
  if (positions.length === 0) {
    return <EmptyState>No target holdings were stored for this signal.</EmptyState>;
  }

  return (
    <div className="holdings-table-wrap">
      <table className="holdings-table">
        <thead>
          <tr>
            <th scope="col">Exchange</th>
            <th scope="col">Symbol</th>
            <th scope="col">Name</th>
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
              <td>{position.name}</td>
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
