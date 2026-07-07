import { FeedbackMessage } from "./FeedbackMessage";

export const Loading = () => (
  <FeedbackMessage variant="loading">Loading dashboard data.</FeedbackMessage>
);

export const Success = () => (
  <FeedbackMessage variant="success">Saved successfully.</FeedbackMessage>
);

export const Error = () => (
  <FeedbackMessage variant="error">Failed to fetch data.</FeedbackMessage>
);

export const Info = () => (
  <FeedbackMessage variant="info">Heads up: market data is stale.</FeedbackMessage>
);

export const WithCustomClassName = () => (
  <FeedbackMessage className="dashboard-alert" variant="error">
    Bootstrap step 2 failed.
  </FeedbackMessage>
);
