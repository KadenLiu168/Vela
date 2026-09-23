import type { DashboardWalkForwardSummary } from "../api/client";
import { Link } from "react-router-dom";
import { DescriptionItem, EmptyState } from "../components";
import { formatDate, formatInteger } from "../utils/formatters";
import { PanelHeading } from "./panelHeading";
import {
  describeOosAvailability,
  deriveOosHeadlines,
  walkForwardStatusLabel
} from "./researchWorkbench";
import { generalizationGapText } from "./walkForwardFormatters";

/** Layer 4 — out-of-sample robustness. Presents the latest walk-forward run as
 *  a research fact: its status, range and window count, and, for a successful
 *  run, the cross-window OOS aggregates from persisted evidence. The complete
 *  evidence (per-window records, parameter stability, stitched path,
 *  provenance) stays in the dedicated Walk-forward flow. No score, rating or
 *  pass/fail verdict is produced here. */
export function OosRobustnessSection({
  isLoading = false,
  walkForward
}: {
  isLoading?: boolean;
  walkForward: DashboardWalkForwardSummary | null;
}) {
  return (
    <section
      aria-label="Out-of-sample robustness"
      className="dashboard-panel research-panel oos-robustness-panel"
    >
      <PanelHeading eyebrow="Robustness" title="OOS evidence" />
      {isLoading ? (
        <EmptyState>Loading walk-forward evidence.</EmptyState>
      ) : walkForward === null ? (
        <>
          <p className="research-note">No walk-forward run exists for the current strategy yet.</p>
          <Link className="operation-link" to="/walk-forwards">
            Start a walk-forward run
          </Link>
        </>
      ) : (
        <WalkForwardEvidence walkForward={walkForward} />
      )}
    </section>
  );
}

function WalkForwardEvidence({ walkForward }: { walkForward: DashboardWalkForwardSummary }) {
  return (
    <>
      <strong className="panel-primary">Walk-forward #{formatInteger(walkForward.run_id)}</strong>
      <dl className="compact-list">
        <DescriptionItem label="Status" value={walkForwardStatusLabel(walkForward.status)} />
        <DescriptionItem
          label="Test range"
          mono value={`${formatDate(walkForward.start_date)} to ${formatDate(walkForward.end_date)}`}
        />
        <DescriptionItem label="Windows" mono value={formatInteger(walkForward.window_count)} />
      </dl>

      {walkForward.oos === null ? (
        <p className="research-note">{describeOosAvailability(walkForward)}</p>
      ) : (
        <>
          <dl aria-label="Cross-window OOS aggregates" className="research-oos-grid">
            {deriveOosHeadlines(walkForward.oos).map((headline) => (
              <div className="research-oos-card" key={headline.label}>
                <dt>{headline.label}</dt>
                <dd>
                  {headline.value}
                  <p className="research-oos-meta">{headline.meta}</p>
                </dd>
              </div>
            ))}
          </dl>
          <div className="research-note-group">
            <p>{generalizationGapText(walkForward.oos.generalization_gap)}</p>
            <p>
              {`Evidence status: ${walkForward.oos.metrics.total_return.evidence_status} — sufficient requires at least three valid windows.`}
            </p>
            <p>
              These are descriptive statistics across the independent per-window OOS estimates; they
              are not a combined capital path.
            </p>
          </div>
        </>
      )}

      <Link className="operation-link" to={`/walk-forwards/${walkForward.run_id}`}>
        View walk-forward evidence
      </Link>
    </>
  );
}
