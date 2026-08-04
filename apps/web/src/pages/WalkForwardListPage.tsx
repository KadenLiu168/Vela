import { useEffect, useState } from "react";
import { ApiClientError, type WalkForwardPageResponse, listWalkForwards } from "../api/client";
import { EmptyState, FeedbackMessage, Pagination } from "../components";
import { formatDate, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 10;

type WalkForwardListState =
  | { status: "loading"; data?: never; error?: never; offset?: never }
  | { status: "ready"; data: WalkForwardPageResponse; error?: never; offset: number }
  | { status: "error"; data?: never; error: string; offset: number };

export function WalkForwardListPage() {
  const [offset, setOffset] = useState(0);
  const [state, setState] = useState<WalkForwardListState>({ status: "loading" });

  useEffect(() => {
    let isCurrent = true;
    listWalkForwards(PAGE_SIZE, offset)
      .then((data) => {
        if (isCurrent) {
          setState({ status: "ready", data, offset });
        }
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setState({
            status: "error",
            error: error instanceof ApiClientError ? error.kind : "unavailable",
            offset
          });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [offset]);

  return (
    <section className="page list-page walk-forward-list-page">
      <div className="page-heading">
        <p>Walk-forward research workspace</p>
        <h1>Walk-forward History</h1>
      </div>
      {renderWalkForwardList(getCurrentListState(state, offset), offset, setOffset)}
    </section>
  );
}

function getCurrentListState(state: WalkForwardListState, offset: number): WalkForwardListState {
  return state.status === "loading" || state.offset === offset ? state : { status: "loading" };
}

function renderWalkForwardList(
  state: WalkForwardListState,
  offset: number,
  setOffset: (value: number) => void
) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading Walk-forward history.</FeedbackMessage>;
  }

  if (state.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Walk-forward history API unavailable: {state.error}
      </FeedbackMessage>
    );
  }

  if (state.data.runs.length === 0 && offset === 0) {
    return (
      <EmptyState>
        No complete Walk-forward evaluation exists yet. Standalone OOS backtests are not inferred as history.
      </EmptyState>
    );
  }

  return (
    <article className="dashboard-panel">
      <div className="holdings-table-wrap">
        <table className="holdings-table">
          <caption className="sr-only">Persisted Walk-forward evaluations</caption>
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Finished</th>
              <th scope="col">Strategy</th>
              <th scope="col">Interval</th>
              <th scope="col">Windows</th>
              <th scope="col">Contracts</th>
              <th scope="col">Checksums</th>
            </tr>
          </thead>
          <tbody>
            {state.data.runs.map((run) => (
              <tr key={run.run_id}>
                <td>
                  <a className="operation-link" href={`/walk-forwards/${run.run_id}`}>
                    #{run.run_id}
                  </a>
                </td>
                <td>{formatTimestamp(run.finished_at)}</td>
                <td>{run.strategy_id}</td>
                <td>{`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`}</td>
                <td>{run.window_count}</td>
                <td>{`${run.provenance_version} / ${run.evidence_version}`}</td>
                <td className="mono-compact">
                  {compactChecksum(run.config_checksum)} / {compactChecksum(run.input_data_checksum)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        offset={offset}
        pageSize={PAGE_SIZE}
        itemCount={state.data.runs.length}
        totalCount={state.data.total}
        onOffsetChange={setOffset}
      />
    </article>
  );
}

function compactChecksum(value: string): string {
  return value.slice(0, 12);
}
