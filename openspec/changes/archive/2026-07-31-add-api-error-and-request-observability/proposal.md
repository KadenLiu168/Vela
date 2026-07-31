## Why

The API currently distinguishes several expected failures through `ValueError`
messages and broad exception catches, so message wording can accidentally change
HTTP behavior and internal invariant failures can be misreported as client
errors. Requests and long-running backend operations also lack a shared
correlation identifier and consistent lifecycle logs, which makes failures hard
to trace without adding a full metrics platform.

## What Changes

- Introduce a small typed domain-exception hierarchy for expected caller and
  local-data failures, and map those types centrally to the existing stable HTTP
  status, code, category, and message contracts.
- Remove API decisions based on exception-message matching and stop treating
  arbitrary `ValueError` instances as expected client errors.
- Assign every API request a request ID, return it in the `X-Request-ID`
  response header, and include it in request completion and exception logs.
- Initialize the existing standard-library logging configuration from backend
  entrypoints and add concise start/completion/failure logs around market-data
  fetching, signal generation, and backtest execution.
- Log unexpected exceptions with diagnostic context while continuing to return
  a generic, non-sensitive error response.
- Add contract tests for typed error mapping, request correlation, safe
  unexpected-error handling, and critical-operation lifecycle logging.
- Keep Prometheus/StatsD metrics, distributed tracing, slow-query monitoring,
  third-party logging frameworks, and resource limits outside this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `http-api-service`: Require type-based error mapping and per-request
  correlation without changing existing successful response bodies or known
  error-envelope contracts.
- `logging-configuration`: Require backend logging initialization and
  structured lifecycle/diagnostic context for critical operations.

## Impact

This change affects selected exception definitions and raise sites in
`packages/core`, API exception handlers and middleware in `apps/api`, backend
entrypoints, and their tests. It depends on
`modularize-and-type-http-api` for the application factory and router layout,
adds no third-party dependency, changes no database schema, and adds only the
`X-Request-ID` response header to the public HTTP surface.
