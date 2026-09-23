import { EmptyState, FeedbackMessage } from "./FeedbackMessage";
import { DescriptionItem } from "./DescriptionItem";

/** Standard research panel: the panel surface role with 24px padding. */
export const StandardPanel = () => (
  <article className="dashboard-panel">
    <div className="panel-heading">
      <h3>Parameters</h3>
      <div className="panel-heading-end">
        <span className="panel-heading-eyebrow">Strategy</span>
      </div>
    </div>
    <strong className="panel-primary">dual_momentum</strong>
    <dl className="compact-list">
      <DescriptionItem label="Version" mono value="v1" />
      <DescriptionItem label="Type" value="dual_momentum" />
      <DescriptionItem label="Trading cost" mono value="10 bps" />
    </dl>
  </article>
);

/** Emphasized metric card: the raised surface role. */
export const EmphasizedMetricPanel = () => (
  <div className="research-headline-grid">
    <dl className="research-headline">
      <dt>Total return</dt>
      <dd>15.43%</dd>
      <p className="research-headline-difference">vs CSI 300 buy-and-hold: +10.86%</p>
    </dl>
  </div>
);

/** Panel loading, empty and error states reuse the shared feedback set. */
export const PanelStates = () => (
  <div className="workflow-grid">
    <article className="dashboard-panel">
      <div className="panel-heading">
        <h3>Loading</h3>
      </div>
      <FeedbackMessage variant="loading">Loading fetch history.</FeedbackMessage>
    </article>
    <article className="dashboard-panel">
      <div className="panel-heading">
        <h3>Fetch history</h3>
      </div>
      <EmptyState>No market data fetch history exists yet.</EmptyState>
    </article>
    <article className="dashboard-panel">
      <div className="panel-heading">
        <h3>Market data</h3>
      </div>
      <FeedbackMessage variant="error">Failed to load market data.</FeedbackMessage>
    </article>
  </div>
);
