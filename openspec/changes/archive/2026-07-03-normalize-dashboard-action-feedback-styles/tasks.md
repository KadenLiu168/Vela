## 1. Dashboard Style Normalization

- [x] 1.1 Normalize Dashboard refresh, operation, empty-state, and Backtest submit button styles to 0px-radius Graphite filled/outlined action variants.
- [x] 1.2 Tokenize Backtest run form labels and inputs with existing color, typography, spacing, background, border, and button-radius variables.
- [x] 1.3 Restyle Dashboard load states, alerts, `FeedbackMessage`, operation summaries, guidance, and operation links to neutral tokenized surfaces with narrow Ember or Brass accents.

## 2. Behavior Preservation

- [x] 2.1 Confirm `FeedbackMessage` preserves `role="status"` and `role="alert"` behavior while supporting the updated visual classes.
- [x] 2.2 Review Dashboard changes to confirm API calls, routes, form validation, and disabled/loading conditions are unchanged.

## 3. Validation

- [x] 3.1 Run OpenSpec validation for `normalize-dashboard-action-feedback-styles`.
- [x] 3.2 Run supported frontend validation commands: `npm --prefix apps/web run lint`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
