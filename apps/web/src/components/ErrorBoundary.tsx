import { Component, type ErrorInfo, type ReactNode } from "react";
import { FeedbackMessage } from "./FeedbackMessage";

type ErrorBoundaryProps = {
  children: ReactNode;
  fallback?: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface the error to the console for now; a future change may
    // forward to an external logger (e.g. Sentry) without changing
    // the boundary's public API.
    console.error("ErrorBoundary caught a render error:", error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback !== undefined) {
        return this.props.fallback;
      }
      return (
        <div className="error-boundary">
          <FeedbackMessage variant="error">
            Something went wrong while rendering this page.
          </FeedbackMessage>
        </div>
      );
    }
    return this.props.children;
  }
}
