import { Link } from "react-router-dom";
import type { WalkForwardDetailResponse } from "../api/client";
import { formatDate, formatInteger } from "../utils/formatters";

type WalkForwardRunHeaderSectionProps = {
  run: WalkForwardDetailResponse["run"];
};

/** First-screen Run Header: navigation back to the Walk-forward history list,
 *  the run status, and a one-line run summary. The run title stays in the
 *  page heading; full execution metadata lives in the provenance region. */
export function WalkForwardRunHeaderSection({ run }: WalkForwardRunHeaderSectionProps) {
  return (
    <header className="run-header">
      <Link className="operation-link" to="/walk-forwards">
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
    </header>
  );
}
