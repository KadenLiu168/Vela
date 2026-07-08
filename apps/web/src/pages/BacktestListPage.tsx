import { useEffect, useState } from "react";
import {
  ApiClientError,
  type BacktestListItem,
  listBacktests
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination } from "../components";
import { formatDate, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 10;

type BacktestListState =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: BacktestListItem[]; error?: never }
  | { status: "error"; data?: never; error: string };

export function BacktestListPage() {
  const [offset, setOffset] = useState(0);
  const [backtestState, setBacktestState] = useState<BacktestListState>({
    status: "loading"
  });

  useEffect(() => {
    let isCurrent = true;

    setBacktestState({ status: "loading" });

    listBacktests(PAGE_SIZE, offset)
      .then((data) => {
        if (isCurrent) {
          setBacktestState({ status: "ready", data: data.runs });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        setBacktestState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable"
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [offset]);

  return (
    <section className="page list-page backtest-list-page">
      <div className="page-heading">
        <p>Backtest research workspace</p>
        <h1>Backtests</h1>
      </div>
      {renderBacktestList(backtestState, offset, setOffset)}
    </section>
  );
}

function renderBacktestList(
  state: BacktestListState,
  offset: number,
  setOffset: (value: number) => void
) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading backtest history.</FeedbackMessage>;
  }

  if (state.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Backtest history API unavailable: {state.error}
      </FeedbackMessage>
    );
  }

  if (state.data.length === 0 && offset === 0) {
    return (
      <EmptyState>
        No local backtest run exists yet. Run a backtest from the Dashboard to see its detail here.
      </EmptyState>
    );
  }

  return (
    <article className="dashboard-panel">
      <div className="holdings-table-wrap">
        <table className="holdings-table">
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Date range</th>
              <th scope="col">Status</th>
              <th scope="col">Started at</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((run) => (
              <tr key={run.run_id}>
                <td>
                  <a className="operation-link" href={`/backtests/${run.run_id}`}>
                    #{run.run_id}
                  </a>
                </td>
                <td>{`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`}</td>
                <td>{run.status}</td>
                <td>{formatTimestamp(run.started_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        offset={offset}
        pageSize={PAGE_SIZE}
        itemCount={state.data.length}
        onOffsetChange={setOffset}
      />
    </article>
  );
}
