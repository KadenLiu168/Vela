import { Link, useLocation } from "react-router-dom";
import {
  type StrategySignalDetailPosition,
  type StrategySignalDetailResponse,
  getStrategySignalDetail
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage, ReadFailure } from "../components";
import { useDocumentTitle } from "../utils/documentTitle";
import { listReturnHref } from "../utils/listReturn";
import { useResource, type ResourceState } from "../utils/useResource";
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

export function SignalDetailPage({ signalId }: SignalDetailPageProps) {
  const location = useLocation();
  const backHref = listReturnHref(location.state, "/signals");
  const { state, reload } = useResource({
    hasNotFoundState: true,
    key: signalId,
    load: () => getStrategySignalDetail(signalId)
  });

  useDocumentTitle(`Signal Detail #${signalId}`);

  return (
    <section className="page detail-page signal-detail-page">
      <div className="page-heading">
        <Link className="operation-link detail-back-link" to={backHref}>
          ← Back to Signals
        </Link>
        <p>Signal research workspace</p>
        <h1>Signal Detail</h1>
      </div>
      {renderSignalDetail(state, signalId, reload)}
    </section>
  );
}

function renderSignalDetail(
  signalState: ResourceState<StrategySignalDetailResponse>,
  signalId: string,
  retry: () => void
) {
  if (signalState.status === "loading") {
    return <FeedbackMessage variant="loading">Loading signal detail.</FeedbackMessage>;
  }

  if (signalState.status === "not-found") {
    return <EmptyState>Signal {signalId} was not found.</EmptyState>;
  }

  if (signalState.status === "error") {
    return <ReadFailure error={signalState.error} label="Signal detail" onRetry={retry} />;
  }

  const signal = signalState.data.signal;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Signal #{signal.signal_id}</strong>
      <dl className="compact-list">
        <DescriptionItem label="Signal date" mono value={formatDate(signal.signal_date)} />
        <DescriptionItem label="Strategy" mono value={signal.strategy_id} />
        <DescriptionItem label="Config version" mono value={signal.config_version} />
        <DescriptionItem label="Result" value={formatNullableText(signal.result)} />
        <DescriptionItem label="Source" value={signal.source} />
        {signal.source === "backtest" && signal.backtest_run_id !== null ? (
          <DescriptionItem
            label="Backtest"
            value={
              <Link className="operation-link" to={`/backtests/${signal.backtest_run_id}`}>
                Backtest #{signal.backtest_run_id}
              </Link>
            }
          />
        ) : null}
        <DescriptionItem label="Fallback" value={formatBoolean(signal.is_fallback)} />
        <DescriptionItem label="Generated at" mono value={formatTimestamp(signal.generated_at)} />
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
              <td className="mono-compact">{position.exchange}</td>
              <td className="mono-compact">{position.symbol}</td>
              <td>{position.name}</td>
              <td className="mono-compact">{formatTargetWeight(position.target_weight)}</td>
              <td className="mono-compact">{formatNullableInteger(position.rank)}</td>
              <td className="mono-compact">{formatDecimal(position.score, 6)}</td>
              <td>{formatBoolean(position.is_fallback)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
