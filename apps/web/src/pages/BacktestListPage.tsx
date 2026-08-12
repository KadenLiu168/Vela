import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiClientError,
  type BacktestListItem,
  listBacktests
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination } from "../components";
import { formatDate, formatDecimal, formatRatioAsPercent, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 10;

type BacktestListState =
  | { status: "loading"; data?: never; error?: never; offset?: never }
  | { status: "ready"; data: BacktestListItem[]; error?: never; offset: number }
  | { status: "error"; data?: never; error: string; offset: number };

export function BacktestListPage() {
  const [offset, setOffset] = useState(0);
  const [backtestState, setBacktestState] = useState<BacktestListState>({
    status: "loading"
  });

  useEffect(() => {
    let isCurrent = true;

    listBacktests(PAGE_SIZE, offset)
      .then((data) => {
        if (isCurrent) {
          setBacktestState({ status: "ready", data: data.runs, offset });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        setBacktestState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          offset
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
      {renderBacktestList(getBacktestListState(backtestState, offset), offset, setOffset)}
    </section>
  );
}

function getBacktestListState(state: BacktestListState, offset: number): BacktestListState {
  return state.status === "loading" || state.offset === offset ? state : { status: "loading" };
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
      <div aria-label="Backtest runs table" className="holdings-table-wrap backtest-list-table-wrap" tabIndex={0}>
        <table className="holdings-table backtest-list-table">
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Date range</th>
              <th scope="col">Status</th>
              <th scope="col">Started at</th>
              <th scope="col">Total return</th>
              <th scope="col">CAGR (calendar-time)</th>
              <th scope="col">Sharpe (daily returns, 252D)</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((run) => (
              <tr key={run.run_id}>
                <td>
                  <Link className="operation-link" to={`/backtests/${run.run_id}`}>
                    #{run.run_id}
                  </Link>
                </td>
                <td>{`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`}</td>
                <td>{run.status}</td>
                <td>{formatTimestamp(run.started_at)}</td>
                <td>{formatRatioAsPercent(run.total_return)}</td>
                <td>{formatRatioAsPercent(run.annualized_return)}</td>
                <td>{formatDecimal(run.sharpe_ratio, 2, false)}</td>
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
