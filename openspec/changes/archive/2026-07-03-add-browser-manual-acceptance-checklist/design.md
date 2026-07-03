## Context

The web frontend already provides Dashboard, Signal Detail, and Backtest Detail routes, plus Dashboard actions for market data fetch, signal generation, and backtest execution. Existing automated validation covers component states and API loops, but there is no single browser checklist for local manual acceptance.

## Goals / Non-Goals

**Goals:**
- Add a concise manual checklist that can be followed from a browser during local frontend validation.
- Cover empty, error, and success states for the workflow areas named by COP-128.
- Clearly label steps that need a running FastAPI service and seeded or real SQLite data.
- Keep the checklist close to operator needs instead of implementation internals.

**Non-Goals:**
- Do not add or change frontend runtime behavior.
- Do not add new API endpoints, database setup logic, or frontend dependencies.
- Do not replace existing automated tests.

## Decisions

- Store the checklist at `docs/browser-manual-acceptance.md`.
  - Alternative: expand `apps/web/README.md`.
  - Rationale: the checklist is a regression artifact, not a setup reference, and an independent docs file keeps README focused.
- Reference existing local commands and routes instead of introducing new scripts.
  - Alternative: add a scripted manual-test launcher.
  - Rationale: COP-128 asks for a manual checklist only; adding scripts would expand scope.
- Treat "real backend data support" as the local FastAPI service plus SQLite data produced by `tests.integration_data` or real workflow execution.
  - Alternative: require production-like external data.
  - Rationale: Phase 1 validation is local-first and should not depend on production infrastructure.

## Risks / Trade-offs

- Checklist can drift from UI labels or routes -> keep steps tied to current page areas and commands, and update alongside future frontend workflow changes.
- Some error states require temporarily stopping the API or using invalid IDs -> document those as local-only actions so they are not confused with normal success validation.
