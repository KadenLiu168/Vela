import { Link } from "react-router-dom";
import type { WalkForwardDetailResponse } from "../api/client";
import { formatDate, formatInteger } from "../utils/formatters";

type WalkForwardRunHeaderSectionProps = {
  backHref: string;
  run: WalkForwardDetailResponse["run"];
};

/** First-screen Run Header: navigation back to the Walk-forward history list,
 *  the run status, and a one-line run summary. The run title stays in the
 *  page heading; full execution metadata lives in the provenance region. */
export function WalkForwardRunHeaderSection({ backHref, run }: WalkForwardRunHeaderSectionProps) {
  return (
    <header className="run-header">
      <Link className="operation-link" to={backHref}>
        ← Back to Walk-forward history
      </Link>
      <p className="run-summary">
        <strong>{run.strategy_id}</strong>
        <span aria-hidden="true"> · </span>
        {formatDate(run.start_date)} to {formatDate(run.end_date)}
        <span aria-hidden="true"> · </span>
        {formatInteger(run.window_count)} {run.window_count === 1 ? "window" : "windows"}
        <span aria-hidden="true"> · </span>
        <span className="run-summary-status">{run.status}</span>
      </p>
      {renderNextStep(run.status)}
    </header>
  );
}

/** A run that has not reached a terminal state has no evidence to show yet, so
 *  the header says what moves it forward rather than leaving the page as a
 *  status with nothing behind it. */
function renderNextStep(status: WalkForwardDetailResponse["run"]["status"]) {
  if (status === "queued") {
    return (
      <p className="detail-note">
        Queued runs are executed by a separate local worker rather than by the API process, so
        this run stays queued until one claims it. Run vela walk-forward-worker to execute it.
      </p>
    );
  }

  if (status === "running") {
    return (
      <p className="detail-note">
        This run is being executed by the local worker. This page does not refresh itself; its
        evidence appears here once the run finishes.
      </p>
    );
  }

  return null;
}
