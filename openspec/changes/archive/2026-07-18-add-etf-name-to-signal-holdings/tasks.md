## 1. Core report layer

- [x] 1.1 Add `name: str` to the `StrategySignalReportPosition` dataclass.
- [x] 1.2 Populate `name` from `etfs_by_id[position.etf_id].name` in `_to_report`.
- [x] 1.3 Update or add core tests asserting the report position carries the ETF name.

## 2. API response

- [x] 2.1 Emit `name` in `_strategy_signal_detail_position_response`.
- [x] 2.2 Emit `name` in `_latest_strategy_signal_position_response`.
- [x] 2.3 Update or add API tests for position serialization on both endpoints.

## 3. Frontend client and UI

- [x] 3.1 Add `name` to the `StrategySignalDetailPosition` and `LatestStrategySignalPosition` types in `apps/web/src/api/client.ts`.
- [x] 3.2 Add a "Name" column (placed immediately after Symbol) to the Signal Detail target holdings table in `apps/web/src/pages/SignalDetailPage.tsx`.
- [x] 3.3 Update frontend tests for the new field: add `name` to mock position objects in `apps/web/src/api/client.test.ts` and `apps/web/src/App.test.tsx`, and update the Signal Detail table render tests for the new column (populated and missing-name cases).

## 4. Validation

- [x] 4.1 Run frontend typecheck, lint, and tests.
- [x] 4.2 Run core and API tests.
- [x] 4.3 Run `openspec validate add-etf-name-to-signal-holdings`.
