## Context

COP-123 targets key frontend test coverage for Phase 1 workflow UI areas. The current React app renders the Dashboard, Signal Detail, and Backtest Detail pages with controlled API fixtures in `apps/web/src/App.test.tsx`, and the relevant UI regions are already accessible through headings, tables, alerts, and status roles.

## Goals / Non-Goals

**Goals:**

- Cover Dashboard status blocks, target holdings, backtest metric cards, and error summaries with controlled frontend fixtures.
- Ensure fixtures continue to mirror the real API response field names and nesting used by the shared API client types.
- Validate loading, empty, and error states for the key component regions through the existing frontend test command.

**Non-Goals:**

- No production UI behavior changes.
- No API, backend, ORM model, migration, or integration fixture changes.
- No new frontend testing dependency or test runner.
- No component extraction solely for test structure.

## Decisions

- Keep coverage in `apps/web/src/App.test.tsx` using route-level renders. This matches the existing test style and verifies component regions through the user-visible DOM rather than private implementation details.
- Use existing fixture factories and targeted fixture overrides. This keeps fixture fields aligned with real API response structures while avoiding a second mock-data layer.
- Scope tests to critical states called out by COP-123. Broader visual regression, screenshot, or browser E2E coverage is outside this COP and would add tooling beyond the issue.

## Risks / Trade-offs

- Page-level tests can become large as coverage grows. Mitigation: add focused assertions around named regions and keep fixture overrides local to each scenario.
- Internal page subcomponents remain unexported. Mitigation: test through accessible DOM boundaries, which is more stable than testing private functions directly.
