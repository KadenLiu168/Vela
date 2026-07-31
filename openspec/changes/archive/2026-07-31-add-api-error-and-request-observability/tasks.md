## 1. Establish Error Contracts

- [x] 1.1 Add failing core and API tests for typed missing-data, invalid-range, and backtest input/data failures, including the existing status, code, category, and safe-message contracts.
- [x] 1.2 Add failing regressions proving exception-message lookalikes and arbitrary `ValueError` instances produce the generic 500 response instead of an expected 4xx response.
- [x] 1.3 Introduce the minimal transport-neutral core exception hierarchy and convert only verified expected-error raise sites.
- [x] 1.4 Centralize FastAPI exception-to-response mappings and remove router message matching and broad `ValueError` translation without changing validation, not-found, or config-error envelopes.

## 2. Add Request Correlation

- [x] 2.1 Add failing ASGI tests for generated, accepted, and rejected caller request IDs across successful, validation, typed-domain, explicit HTTP, and unexpected-error responses.
- [x] 2.2 Implement request-ID validation/generation middleware, request-state propagation, and the `X-Request-ID` response header in the application factory created by `modularize-and-type-http-api`.
- [x] 2.3 Add failing log-capture tests proving each request emits one bounded completion event with matching request ID, method, normalized route, status, and duration while excluding body and raw query values.
- [x] 2.4 Implement request completion logging and correlated unexpected-exception diagnostics with one server-side stack trace and a generic client response.

## 3. Instrument Critical Backend Workflows

- [x] 3.1 Add failing log-capture tests for market-data fetch, current/historical signal generation, and backtest start/completion events, bounded counts, identifiers, and durations.
- [x] 3.2 Initialize shared logging explicitly from API and CLI executable entrypoints and add an import-side-effect regression test.
- [x] 3.3 Add standard-library lifecycle logs at the critical workflow boundaries using monotonic timing and stable event names.
- [x] 3.4 Add a long-history or multi-row regression proving lifecycle logging is not emitted once per price row, holding, ETF, or rebalance date.

## 4. Verify Contracts and Quality

- [x] 4.1 Run focused core and API tests covering every delta-spec scenario, including header/body compatibility and log redaction.
- [x] 4.2 Run the complete Python gate: `uv sync --group dev`, Ruff check, Ruff format check, mypy, and the full pytest suite.
- [x] 4.3 Validate this Change and all OpenSpec content strictly, run `openspec doctor`, and inspect the final scoped diff for undeclared dependencies or behavior.
