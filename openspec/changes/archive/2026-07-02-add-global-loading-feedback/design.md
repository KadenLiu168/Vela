## Context

The React frontend currently renders Dashboard, Signal Detail, and Backtest Detail through the shared API client. Dashboard has operation-specific pending booleans and result summaries, while detail pages render simple text loading states. COP-115 requires the first-phase frontend to make those states explicit and consistent across page loads and long-running operations without changing backend APIs.

## Goals / Non-Goals

**Goals:**

- Provide one small shared feedback component for page loading, operation loading, success, and failure messages.
- Use the shared feedback pattern on Dashboard, Signal Detail, and Backtest Detail page data loads.
- Treat Dashboard market data fetch, signal generation, and backtest run as mutually exclusive long-running operations to prevent conflicting user submissions.
- Preserve existing operation result details after success or failure.
- Cover the behavior with focused frontend tests.

**Non-Goals:**

- No backend API contract changes.
- No background job status polling or progress percentages.
- No global app-wide state manager.
- No new notification library or dependency.
- No redesign of the Dashboard layout.

## Decisions

- Add a small shared `FeedbackMessage` component rather than a toast system.
  - Rationale: the app is a local research tool with a compact first-phase UI, and scoped inline feedback is already the established pattern.
  - Alternative considered: add a global toast provider. That would introduce broader state and visual behavior than COP-115 needs.

- Track one Dashboard `activeOperation` value for the three long-running actions.
  - Rationale: market data fetch, signal generation, and backtest run can all refresh or depend on the same Dashboard data. A single active operation gives basic concurrency protection without changing API calls.
  - Alternative considered: keep separate booleans only. That prevents duplicate clicks per action but still allows conflicting operations to run together.

- Keep operation completion feedback inside the Operations panel.
  - Rationale: existing summaries already show API response details and links. Reusing that location avoids an additional notification surface.
  - Alternative considered: show completion feedback in the page header. That would be less specific for operation response details.

## Risks / Trade-offs

- Operation mutual exclusion is coarse-grained and blocks unrelated operations while one request is pending -> Acceptable for Phase 1 because these actions are long-running local workflows and share Dashboard refresh state.
- Inline feedback is less transient than toast notifications -> Mitigated by keeping the latest operation result visible until the next operation starts.
- The shared component can still be styled differently by context -> Mitigated by limiting variants to loading, success, error, and info.
