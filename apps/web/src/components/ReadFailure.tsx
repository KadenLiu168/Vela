import { FeedbackMessage } from "./FeedbackMessage";
import { describeReadFailure } from "../utils/readFailure";

type ReadFailureProps = {
  /** What could not be loaded, e.g. "Signal history". */
  label: string;
  error: unknown;
  onRetry: () => void;
};

export function ReadFailure({ label, error, onRetry }: ReadFailureProps) {
  return (
    <FeedbackMessage className="dashboard-alert read-failure" variant="error">
      <p className="read-failure-message">
        {label} could not be loaded. {describeReadFailure(error)}
      </p>
      <button className="button-secondary read-failure-retry" onClick={onRetry} type="button">
        Retry
      </button>
    </FeedbackMessage>
  );
}
