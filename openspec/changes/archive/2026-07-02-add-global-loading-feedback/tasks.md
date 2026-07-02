## 1. Tests

- [x] 1.1 Add frontend tests for shared page-loading feedback on Dashboard, Signal Detail, and Backtest Detail.
- [x] 1.2 Add frontend tests that each Dashboard operation shows pending feedback and disables the other long-running operation controls while pending.
- [x] 1.3 Add frontend tests that success and failure feedback remains visible after each Dashboard operation completes.

## 2. Implementation

- [x] 2.1 Add a shared frontend feedback component and styles for loading, success, error, and info states.
- [x] 2.2 Update Dashboard page loading, operation pending, success, and failure rendering to use the shared feedback component.
- [x] 2.3 Replace separate Dashboard action guards with a single active-operation guard that prevents duplicate and conflicting submissions.
- [x] 2.4 Update Signal Detail and Backtest Detail page loading states to use the shared feedback component.

## 3. Validation

- [x] 3.1 Run focused frontend tests for COP-115 feedback behavior.
- [x] 3.2 Run frontend test, lint, typecheck, and build validation commands.
- [x] 3.3 Run OpenSpec validation/status checks for `add-global-loading-feedback`.
