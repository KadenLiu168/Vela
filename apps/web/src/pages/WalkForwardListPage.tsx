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
  | { status: "refreshing"; message: string }
  | { status: "queued"; runId: number }
  | { status: "running"; runId: number }
  | { status: "failed"; message: string };

export function WalkForwardListPage() {
  const [offset, setOffset] = useState(0);
  const [state, setState] = useState<WalkForwardListState>({ status: "loading" });
  const [runState, setRunState] = useState<RunTriggerState>({ status: "idle" });
  const [refreshToken, setRefreshToken] = useState(0);
  const activeRunId =
    runState.status === "queued" || runState.status === "running" ? runState.runId : null;

  useEffect(() => {
    let isCurrent = true;
    listWalkForwards(PAGE_SIZE, offset)
      .then((data) => {
        if (isCurrent) {
          setState({ status: "ready", data, offset });
          const active = data.runs.find(
            (run) => run.status === "queued" || run.status === "running"
          );
          setRunState((current) => {
            if (current.status === "starting") {
              return current;
            }
            if (active?.status === "queued" || active?.status === "running") {
              return { status: active.status, runId: active.run_id };
            }
            return current.status === "queued" ||
              current.status === "running" ||
              current.status === "refreshing"
              ? { status: "idle" }
              : current;
          });
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
  }, [offset, refreshToken]);

  // Poll the running run every 5s, pausing while the document is hidden.
  useEffect(() => {
    if (activeRunId === null) {
      return;
    }

    let stopped = false;
    let timerId: number | undefined;

    const poll = async () => {
      try {
        const detail = await getWalkForwardDetail(String(activeRunId));
        if (stopped) {
          return;
        }
        if (detail.run.status === "success") {
          setRunState({ status: "idle" });
          navigateToDetail(activeRunId);
        } else if (detail.run.status === "failed") {
          setRunState({
            status: "failed",
            message: detail.run.error_message ?? "Walk-forward run failed."
          });
        } else {
          setRunState({ status: detail.run.status, runId: activeRunId });
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

    if (!document.hidden) {
      schedule();
    }
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      stopped = true;
      if (timerId !== undefined) {
        window.clearTimeout(timerId);
      }
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [activeRunId]);

  async function handleRunClick() {
    if (
      runState.status === "starting" ||
      runState.status === "refreshing" ||
      runState.status === "queued" ||
      runState.status === "running"
    ) {
      return;
    }
    setRunState({ status: "starting" });
    try {
      const accepted = await runWalkForward();
      setRunState({ status: accepted.status, runId: accepted.walk_forward_run_id });
    } catch (error: unknown) {
      if (error instanceof ApiClientError && error.status === 409) {
        setRunState({
          status: "refreshing",
          message: "A walk-forward run is already in progress for this strategy."
        });
        setRefreshToken((value) => value + 1);
      } else {
        const message =
          error instanceof ApiClientError && error.kind === "http"
            ? error.message
            : "Unable to start walk-forward run.";
        setRunState({ status: "failed", message });
      }
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
        className="button-secondary"
        disabled={
          runState.status === "starting" ||
          runState.status === "refreshing" ||
          runState.status === "queued" ||
          runState.status === "running"
        }
        onClick={onRun}
        type="button"
      >
        {runState.status === "queued"
          ? `Queued walk-forward #${runState.runId}…`
          : runState.status === "running"
            ? `Running walk-forward #${runState.runId}…`
            : "Run walk-forward"}
      </button>
      {runState.status === "queued" || runState.status === "running" ? (
        <FeedbackMessage variant="loading">
          {runState.status === "queued"
            ? "Walk-forward queued; waiting for the supervised worker."
            : "Walk-forward running; this page updates automatically."}
        </FeedbackMessage>
      ) : null}
      {runState.status === "failed" ? (
        <FeedbackMessage className="dashboard-alert" variant="error">
          {runState.message}
        </FeedbackMessage>
      ) : null}
      {runState.status === "refreshing" ? (
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
