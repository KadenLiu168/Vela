## Why

Browser-side validation currently relies on scattered frontend tests and ad hoc local checks. A focused manual acceptance checklist is needed so future local validation and regression passes consistently cover the Phase 1 frontend workflow.

## What Changes

- Add a browser manual acceptance checklist for the local web frontend workflow.
- Cover Dashboard, market data fetch, signal generation, backtest execution, Signal Detail, and Backtest Detail checks.
- Include empty, error, and success states for each relevant workflow area.
- Mark checklist steps that require a running local API service and seeded or real backend SQLite data.
- Keep the change documentation-only; do not change frontend runtime behavior or API contracts.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-frontend-app`: Require a browser manual acceptance checklist for the local frontend workflow.

## Impact

- Affected docs: `docs/browser-manual-acceptance.md`, `apps/web/README.md`
- Affected specs: `openspec/specs/web-frontend-app/spec.md`
- Affected code/APIs/dependencies: none
