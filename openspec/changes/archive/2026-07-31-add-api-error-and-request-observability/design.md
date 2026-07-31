## Context

FastAPI currently contains several local exception translations. Some recognize
business failures by matching `ValueError` text, while the backtest endpoint
maps every `ValueError` to HTTP 400. This couples transport behavior to wording
and can hide programming or invariant failures. The unexpected-exception path
returns a safe response but does not emit enough correlated diagnostics.

The core package already exposes `setup_logging()` and the API engineering
change `modularize-and-type-http-api` introduces an application factory,
lifespan configuration, and domain routers. This change builds on that layout;
it must not recreate the application structure or alter successful response
models.

## Goals / Non-Goals

**Goals:**

- Make expected API failures explicit through a minimal domain-exception
  hierarchy and type-based HTTP mapping.
- Preserve existing status codes and stable error bodies for already-specified
  failure cases.
- Give every request a safe correlation ID that is visible to callers and in
  backend logs.
- Emit useful, bounded lifecycle logs for market-data fetches, signal
  generation, and backtests using the standard library.
- Preserve generic client responses while recording stack traces for unexpected
  failures.

**Non-Goals:**

- Introducing `structlog`, OpenTelemetry, Prometheus, StatsD, or another
  dependency.
- Defining alert thresholds, slow-query detection, distributed traces, or
  dashboards.
- Adding background jobs, request timeouts, cancellation, or resource limits.
- Converting every existing `ValueError`; invariant and programming errors
  intentionally remain unexpected.
- Logging request bodies, query values, credentials, portfolio details, price
  rows, or one event per loop iteration.

## Decisions

### 1. Use a small semantic exception hierarchy in core

`VelaError` will be the domain base, with narrow types for expected conditions
that callers can act on, including invalid date ranges, missing market data, and
backtest data/input failures. Exception classes describe domain meaning only;
they do not contain HTTP status codes.

Only raise sites that represent established, expected API outcomes will be
converted. Internal invariants and unclassified `ValueError` instances will
continue to reach the unexpected-error handler.

This is preferred over attaching HTTP metadata to core exceptions because the
core package is also used by the CLI. It is preferred over a single generic
business exception because distinct types make mappings and tests explicit.

### 2. Centralize type-to-HTTP mapping and preserve contracts

The API exception module will own the mapping from domain types to status, error
code, category, and safe message. Known contracts such as `no_market_data`,
`invalid_date_range`, `validation_error`, `not_found`, and `config_error` retain
their existing semantics. Router-level string comparisons and broad
`except ValueError` translations will be removed.

FastAPI validation and intentional `HTTPException` responses remain centrally
formatted. Unexpected exceptions return the existing generic 500 envelope and
are logged with a stack trace. This avoids exposing implementation details while
making diagnostics available locally.

### 3. Correlate requests with one response header

Middleware will assign a request ID before routing. A caller-provided
`X-Request-ID` is reused only when it is a non-empty, bounded token containing
safe ASCII letters, digits, `.`, `_`, or `-`; otherwise a generated UUID is
used. The effective value is stored on request state, returned as
`X-Request-ID` on success and error responses, and added to request logs.

The stable JSON error envelope is not extended with a request-ID field. The
header supplies correlation without changing established response bodies or
the typed response models from the preceding API change.

### 4. Log stable events with bounded key-value context

The existing Python `logging` setup remains the only logging mechanism.
Backend executable entrypoints initialize it explicitly; importing a module
does not mutate global logging configuration.

The request middleware emits one completion event with `request_id`, HTTP
method, normalized route template when available, status, and monotonic
`duration_ms`. Critical core workflows emit start and completion events with
operation-specific identifiers, counts, and duration; expected failures may
emit a concise warning. Unexpected stack traces are emitted once at the API
boundary. Values with unbounded cardinality or sensitive content are excluded.

Stable event names and `key=value` fields make logs searchable without adding a
structured-logging dependency. Monotonic timing avoids wall-clock adjustments.

### 5. Implement after the API modularization change

Implementation starts from the application factory, lifespan, routers, and
response models created by `modularize-and-type-http-api`. Middleware and
handlers are registered once by the factory, while individual routers raise
typed domain errors or intentional `HTTPException` values.

This ordering avoids editing the current monolithic `main.py` only to move the
same code immediately afterward.

## Risks / Trade-offs

- **[Some legacy `ValueError` remains ambiguous]** → Convert only verified
  expected outcomes and add regression tests proving all other values produce
  a safe 500.
- **[Caller-provided IDs could pollute logs]** → Enforce a conservative
  character set and length; generate a UUID for invalid input.
- **[Middleware order could omit headers on errors]** → Exercise validation,
  typed-domain, explicit HTTP, and unexpected failures through full ASGI
  integration tests.
- **[Logging adds noise or hot-loop overhead]** → Log once per operation
  boundary, never per price row, holding, or rebalance date.
- **[Duplicate exception logging obscures incidents]** → Put unexpected stack
  traces at the API boundary and keep core completion/failure logging bounded.
- **[Two active changes overlap API files]** → Apply and validate
  `modularize-and-type-http-api` first, then rebase this change on its final
  module layout.

## Migration Plan

1. Apply and verify `modularize-and-type-http-api`.
2. Add domain exceptions and replace only verified expected-error raise sites.
3. Add centralized API mappings, request correlation, and logging
   initialization.
4. Add workflow lifecycle logs and contract tests.
5. Run the complete Python gate and strict OpenSpec validation.

Rollback removes the middleware, handlers, workflow logs, and typed raise-site
changes together. There is no data or schema migration.

## Open Questions

None. Metrics and production tracing are intentionally deferred until a
deployment or scale requirement supplies concrete operational targets.
