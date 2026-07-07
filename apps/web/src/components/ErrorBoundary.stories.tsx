import { Component } from "react";
import { ErrorBoundary } from "./ErrorBoundary";
import { FeedbackMessage } from "./FeedbackMessage";

export const HappyPath = () => (
  <ErrorBoundary>
    <div style={{ padding: "1em", border: "1px solid var(--color-graphite)" }}>
      Children render normally when nothing throws.
    </div>
  </ErrorBoundary>
);

// A sibling component that throws on render so the ErrorBoundary
// catches it. Pattern from React docs:
// https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
class BuggyCounter extends Component<{ throwAt?: number }, { count: number }> {
  state = { count: 0 };
  render() {
    if (this.state.count >= (this.props.throwAt ?? 1)) {
      throw new Error("I crashed!");
    }
    return (
      <button
        onClick={() => this.setState({ count: this.state.count + 1 })}
        style={{ padding: "0.5em 1em" }}
      >
        Click me to crash (after {(this.props.throwAt ?? 1) - 1} more click{((this.props.throwAt ?? 1) - 1) === 1 ? "" : "s"})
      </button>
    );
  }
}

export const DefaultFallback = () => (
  <ErrorBoundary>
    <BuggyCounter />
  </ErrorBoundary>
);

const customFallback = (
  <FeedbackMessage variant="info">
    A custom fallback rendered when an error occurred.
  </FeedbackMessage>
);

export const CustomFallback = () => (
  <ErrorBoundary fallback={customFallback}>
    <BuggyCounter throwAt={2} />
  </ErrorBoundary>
);
