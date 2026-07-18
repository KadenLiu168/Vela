## Why

The Signal Detail target holdings table shows each ETF position's exchange, symbol, target weight, rank, score, and fallback status, but not the ETF's human-readable name. Symbol-only identifiers are unambiguous to domain experts but hurt readability for the broader set of ETFs in the universe; the name gives immediate context about what each holding actually is.

The ETF name is already joined from `etf_info` when the report is built — `etf_info.name` is fetched in the same lookup that produces `exchange` and `symbol`, but is simply not carried into `StrategySignalReportPosition`. So exposing it is a low-risk, additive change with no schema migration.

## What Changes

- Add a `name` field to `StrategySignalReportPosition` (core report layer), sourced from the joined `etf_info.name`. This dataclass is shared by both the by-id detail report and the latest signal report, so one change covers both endpoints.
- Include `name` in the position response of `GET /api/strategy-signals/{signal_id}` and `GET /api/strategy-signals/latest`.
- Add `name` to the `StrategySignalDetailPosition` and `LatestStrategySignalPosition` API client types.
- Render a new "Name" column in the Signal Detail target holdings table, kept as a dedicated column separate from the existing Symbol/Exchange columns (per agreed presentation).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Extend the Signal Detail target holdings table to include an ETF name column.
- `http-api-service`: Extend the strategy signal detail and latest endpoints' position objects to include the ETF `name`.

## Impact

- Core report model in `packages/core/src/vela_core/strategy_signal_report.py`.
- API response builders in `apps/api/src/vela_api/main.py`.
- Frontend API client types in `apps/web/src/api/client.ts`.
- Frontend table rendering in `apps/web/src/pages/SignalDetailPage.tsx`.
- Core, API, and frontend tests covering position serialization and the holdings table.
- OpenSpec `web-frontend-app` and `http-api-service` delta specs.
