import { useEffect, useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  type BacktestListItem,
  listBacktests
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination, ReadFailure } from "../components";
import { useDocumentTitle } from "../utils/documentTitle";
import { isValidListOffset, listHrefWith, listOffsetFrom } from "../utils/listQuery";
import { useResource, type LoadableResourceState } from "../utils/useResource";
import { formatDate, formatDecimal, formatRatioAsPercent, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 10;

export function BacktestListPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const rawOffset = searchParams.get("offset");
  const offset = listOffsetFrom(rawOffset);
  const listHref = `${location.pathname}${location.search}`;
  const { state: backtestState, reload } = useResource({
    key: offset,
    load: () => listBacktests(PAGE_SIZE, offset).then((data) => data.runs)
  });

  useDocumentTitle("Backtests");

  useEffect(() => {
    if (rawOffset !== null && !isValidListOffset(rawOffset)) {
      navigate(listHrefWith(location, { offset: null }), { replace: true });
    }
  }, [rawOffset, location, navigate]);

  function selectOffset(nextOffset: number) {
    const next = Math.max(0, nextOffset);
    navigate(listHrefWith(location, { offset: next === 0 ? null : String(next) }));
  }

  return (
    <section className="page list-page backtest-list-page">
      <div className="page-heading">
        <p>Backtest research workspace</p>
        <h1>Backtests</h1>
      </div>
      {renderBacktestList(backtestState, offset, selectOffset, reload, listHref)}
    </section>
  );
}

function renderBacktestList(
  state: LoadableResourceState<BacktestListItem[]>,
  offset: number,
  setOffset: (value: number) => void,
  retry: () => void,
  listHref: string
) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading backtest history.</FeedbackMessage>;
  }

  if (state.status === "error") {
    return <ReadFailure error={state.error} label="Backtest history" onRetry={retry} />;
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
                <td className="mono-compact">
                  <Link
                    className="operation-link"
                    state={{ listHref }}
                    to={`/backtests/${run.run_id}`}
                  >
                    #{run.run_id}
                  </Link>
                </td>
                <td className="mono-compact">{`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`}</td>
                <td>{run.status}</td>
                <td className="mono-compact">{formatTimestamp(run.started_at)}</td>
                <td className="mono-compact">{formatRatioAsPercent(run.total_return)}</td>
                <td className="mono-compact">{formatRatioAsPercent(run.annualized_return)}</td>
                <td className="mono-compact">{formatDecimal(run.sharpe_ratio, 2, false)}</td>
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
