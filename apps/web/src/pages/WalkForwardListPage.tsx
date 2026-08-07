import { useEffect, useState } from "react";
import {
  ApiClientError,
  type WalkForwardPageResponse,
  getWalkForwardDetail,
  listWalkForwards,
  runWalkForward
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination } from "../components";
import { formatDate, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 10;
const POLL_INTERVAL_MS = 5000;

type WalkForwardListState =
  | { status: "loading"; data?: never; error?: never; offset?: never }
  | { status: "ready"; data: WalkForwardPageResponse; error?: never; offset: number }
  | { status: "error"; data?: never; error: string; offset: number };

type RunTriggerState =
  | { status: "idle" }
  | { status: "starting" }
  | { status: "running"; runId: number }
  | { status: "failed"; message: string };

export function WalkForwardListPage() {
  const [offset, setOffset] = useState(0);
  const [state, setState] = useState<WalkForwardListState>({ status: "loading" });
  const [runState, setRunState] = useState<RunTriggerState>({ status: "idle" });
  const runningRunId = runState.status === "running" ? runState.runId : null;

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

  // Poll the running run every 5s, pausing while the document is hidden.
  useEffect(() => {
    if (runningRunId === null) {
      return;
    }

    let stopped = false;
    let timerId: number | undefined;

    const poll = async () => {
      try {
        const detail = await getWalkForwardDetail(String(runningRunId));
        if (stopped) {
          return;
        }
        if (detail.run.status === "success") {
          setRunState({ status: "idle" });
          navigateToDetail(runningRunId);
        } else if (detail.run.status === "failed") {
          setRunState({
            status: "failed",
            message: detail.run.error_message ?? "Walk-forward run failed."
          });
        }
      } catch {
        // Transient poll failure: keep polling until the run terminal state.
      }
    };

    const schedule = () => {
      timerId = window.setTimeout(() => {
        void poll().finally(() => {
          if (!stopped && !document.hidden) {
            schedule();
          }
        });
      }, POLL_INTERVAL_MS);
    };

    const handleVisibility = () => {
      if (document.hidden) {
        if (timerId !== undefined) {
          window.clearTimeout(timerId);
          timerId = undefined;
        }
      } else {
        void poll().finally(() => {
          if (!stopped && !document.hidden) {
            schedule();
          }
        });
      }
    };

    schedule();
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      stopped = true;
      if (timerId !== undefined) {
        window.clearTimeout(timerId);
      }
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [runningRunId]);

  async function handleRunClick() {
    if (runState.status === "starting" || runState.status === "running") {
      return;
    }
    setRunState({ status: "starting" });
    try {
      const accepted = await runWalkForward();
      setRunState({ status: "running", runId: accepted.walk_forward_run_id });
    } catch (error: unknown) {
      const message =
        error instanceof ApiClientError && error.status === 409
          ? "A walk-forward run is already in progress for this strategy."
          : error instanceof ApiClientError && error.kind === "http"
            ? error.message
            : "Unable to start walk-forward run.";
      setRunState({ status: "failed", message });
    }
  }

  return (
    <section className="page list-page walk-forward-list-page">
      <div className="page-heading">
        <p>Walk-forward research workspace</p>
        <h1>Walk-forward History</h1>
      </div>
      {renderRunTrigger(runState, handleRunClick)}
      {renderWalkForwardList(getCurrentListState(state, offset), offset, setOffset)}
    </section>
  );
}

function renderRunTrigger(runState: RunTriggerState, onRun: () => void) {
  return (
    <div className="walk-forward-run-trigger">
      <button
        className="action-button"
        disabled={runState.status === "starting" || runState.status === "running"}
        onClick={onRun}
        type="button"
      >
        {runState.status === "running"
          ? `Running walk-forward #${runState.runId}…`
          : "Run walk-forward"}
      </button>
      {runState.status === "running" ? (
        <FeedbackMessage variant="loading">
          Running walk-forward; expected 11-30 minutes. This page updates automatically.
        </FeedbackMessage>
      ) : null}
      {runState.status === "failed" ? (
        <FeedbackMessage className="dashboard-alert" variant="error">
          {runState.message}
        </FeedbackMessage>
      ) : null}
    </div>
  );
}

function getCurrentListState(state: WalkForwardListState, offset: number): WalkForwardListState {
  return state.status === "loading" || state.offset === offset ? state : { status: "loading" };
}

function navigateToDetail(runId: number) {
  const nextPath = `/walk-forwards/${runId}`;
  if (window.location.pathname !== nextPath) {
    window.history.pushState({}, "", nextPath);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }
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
              <th scope="col">Status</th>
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
                <td>{run.status}</td>
                <td>{run.finished_at === null ? "—" : formatTimestamp(run.finished_at)}</td>
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
