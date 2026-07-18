## Context

The Signal Detail page (`apps/web/src/pages/SignalDetailPage.tsx`) fetches a signal by id via `GET /api/strategy-signals/{signal_id}` and renders a per-position target holdings table. The backend builds `StrategySignalReport` in `packages/core/src/vela_core/strategy_signal_report.py`, joining each `strategy_signal_position.etf_id` to `etf_info` to obtain `exchange` and `symbol`. The `etf_info.name` field is fetched in the same join (`etfs_by_id[position.etf_id]`) but is not carried into `StrategySignalReportPosition`, so it never reaches the API response or the frontend.

The latest signal endpoint (`GET /api/strategy-signals/latest`) uses the same `get_latest_strategy_signal_report` → `_to_report` builder, so a single change to `StrategySignalReportPosition` benefits both endpoints with no duplication.

## Goals / Non-Goals

**Goals:**

- Expose the ETF `name` on signal position responses for both the detail and latest endpoints.
- Render a dedicated "Name" column in the Signal Detail target holdings table.
- Keep the change additive: no database migration, no removal of existing fields, no breaking API contract change.

**Non-Goals:**

- No rename or removal of the existing Symbol/Exchange columns.
- No change to the Dashboard's use of the latest endpoint (it only consumes `positions.length` today); no new UI for the latest endpoint.
- No change to the CLI signal report output format (out of scope for this web-facing fix).
- No filtering, sorting, search, or pagination changes to the holdings table.

## Decisions

- Add `name: str` to `StrategySignalReportPosition` and populate it from `etfs_by_id[position.etf_id].name` in `_to_report`.
  - Rationale: single source of truth. Both the detail and latest reports flow through this dataclass, so one field addition covers both endpoints.
- Emit `name` in both `_strategy_signal_detail_position_response` and `_latest_strategy_signal_position_response`.
  - Rationale: keep the two position response shapes aligned and avoid an asymmetric "one endpoint has name, the other hides it" footgun. The marginal cost is ~3 lines per builder.
- Add `name` to the `StrategySignalDetailPosition` and `LatestStrategySignalPosition` TypeScript types.
  - Rationale: typed end-to-end so the frontend (and any future consumer) receive the field safely.
- Render Name as a dedicated column placed immediately after the Symbol column.
  - Rationale: groups the identifier columns (Exchange, Symbol, Name) together and keeps Target weight / Rank / Score / Fallback in their current relative order with zero reordering of existing columns. Minimal layout churn.
- Keep the `LatestStrategySignalPosition` `name` field unused by the UI for now.
  - Rationale: the Dashboard only reads `positions.length` from the latest endpoint. The field is added for API consistency and future consumers, with no behavior change today (YAGNI-acknowledged investment).

## Risks / Trade-offs

- ETF names can be long (e.g., "Vanguard Total Stock Market ETF"). The existing horizontally scrollable table wrapper handles overflow; the Name column may widen the leading columns. Acceptable and already handled by the scroll wrapper.
- `etf_info.name` is declared `nullable=False`, so a joined position always has a name. Risk of missing name is negligible.
- Adding `name` to the latest endpoint response increases payload size slightly; the Dashboard ignores it, so there is no behavior change.
- The holdings table is rendered from the by-id endpoint, which is the authoritative source for the detail page (the page fetches by id, not latest). Both endpoints gain the field for consistency.
- Making `name` a required field on the `StrategySignalDetailPosition` and `LatestStrategySignalPosition` TypeScript types will break existing mock position objects in `apps/web/src/api/client.test.ts` and `apps/web/src/App.test.tsx` (they currently construct positions without `name`). Those mocks must be updated together with the table render tests; the frontend test-update task covers all of them, not only the Signal Detail table test.
