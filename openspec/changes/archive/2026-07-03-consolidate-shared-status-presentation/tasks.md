## 1. Focused Coverage

- [x] 1.1 Add or update focused frontend tests that verify shared feedback roles/classes and representative empty-state presentation hooks.

## 2. Shared Presentation

- [x] 2.1 Consolidate shared `FeedbackMessage`, `.empty-state`, and `.dashboard-load-state-*` styles around tokenized neutral surfaces and narrow accents.
- [x] 2.2 Apply shared presentation hooks to existing Dashboard, Signal Detail, and Backtest Detail loading, error, status, and empty states without changing behavior or copy meaning.

## 3. Review and Validation

- [x] 3.1 Review the diff for COP-135 scope, accessibility semantics, business/API/route preservation, and broad chromatic-block regressions.
- [x] 3.2 Run OpenSpec validation for `consolidate-shared-status-presentation`.
- [x] 3.3 Run available frontend validation commands: `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build` from `apps/web`, or document unavailable scripts.
