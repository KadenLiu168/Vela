import { EmptyState } from "./FeedbackMessage";

export const Default = () => (
  <EmptyState>No market data fetch history exists yet.</EmptyState>
);

export const InPanel = () => (
  <div className="dashboard-panel" style={{ padding: "1em" }}>
    <EmptyState>No local market prices are stored yet.</EmptyState>
  </div>
);

export const WithCustomClassName = () => (
  <EmptyState className="market-empty-state">
    Fetch market data to populate dashboard coverage.
  </EmptyState>
);
