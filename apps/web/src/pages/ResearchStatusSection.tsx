import type { DashboardResponse } from "../api/client";
import { PanelHeading } from "./panelHeading";
import { deriveResearchFacts, selectNextResearchAction } from "./researchWorkbench";

/** Layer 1 — current state. States what the research currently has, what lags
 *  the available market data, and the single next action. Every value is a
 *  date or a status from the aggregate; no performance value is derived here,
 *  and the next action links to the pre-existing operation control instead of
 *  duplicating its trigger. */
export function ResearchStatusSection({ data }: { data: DashboardResponse }) {
  const facts = deriveResearchFacts(data);
  const nextAction = selectNextResearchAction(data, facts);

  return (
    <section
      aria-label="Current research state"
      className="dashboard-panel research-panel research-status-panel"
    >
      <PanelHeading eyebrow="Research" title="Current state" />
      <dl className="research-fact-list">
        {facts.map((fact) => (
          <div className="research-fact" key={fact.key}>
            <dt>{fact.label}</dt>
            <dd>
              <span className="research-fact-value">{fact.value}</span>
              {fact.lagCalendarDays === null ? null : (
                <span className="research-fact-lag">
                  {`${fact.lagCalendarDays} calendar days behind the stored market data`}
                </span>
              )}
            </dd>
          </div>
        ))}
      </dl>
      {nextAction === null ? (
        <p className="research-next-action">
          Market data and the latest signal are current; no corrective action is needed.
        </p>
      ) : (
        <p className="research-next-action">
          <span>Next: </span>
          <a className="operation-link" href={`#${nextAction.targetId}`}>
            {nextAction.label}
          </a>
        </p>
      )}
    </section>
  );
}
