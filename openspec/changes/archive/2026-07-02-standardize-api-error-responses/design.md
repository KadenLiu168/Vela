## Context

FastAPI currently returns a mix of default validation payloads, `HTTPException.detail` strings, and uncaught exception responses. The frontend shared client normalizes HTTP status and message, but cannot reliably distinguish validation, not-found, operation-failed, and unexpected errors.

## Goals / Non-Goals

**Goals:**

- Return a stable JSON error envelope for API failures.
- Keep existing successful response shapes unchanged.
- Classify frontend API errors into the four categories required by COP-117.
- Validate representative real backend routes and exception paths through `TestClient`.

**Non-Goals:**

- Change database models, migrations, endpoint URLs, or successful response contracts.
- Add new frontend pages or change operation workflows beyond error display.
- Introduce external error-reporting dependencies.

## Decisions

- Use one API error envelope: `{"error": {"code": string, "category": string, "message": string}}`.
  - Rationale: this keeps the frontend parser simple and leaves room for stable codes without exposing Python exception classes.
  - Alternative considered: keep FastAPI `detail` and infer from status. That cannot distinguish operation failures from generic bad requests.

- Map FastAPI validation failures to `category: "validation"` and status `422`.
  - Rationale: validation is framework-provided and should remain distinguishable from user operation failures.
  - Alternative considered: convert validation failures to status `400`. That would change FastAPI semantics more than necessary.

- Map missing resources to `category: "not_found"` and status `404`.
  - Rationale: existing Backtest Detail behavior already uses 404; this makes the body stable.

- Map expected domain/operation failures to `category: "operation_failed"` and status `400` or `500` depending on the route.
  - Rationale: no local market prices, invalid backtest date ranges, configuration errors, and provider/workflow failures are actionable operation outcomes for the local workflow.

- Map unhandled exceptions to `category: "unexpected"` and status `500`.
  - Rationale: the frontend can show a readable fallback while avoiding implementation details in the response.

## Risks / Trade-offs

- Existing tests expect `{"detail": ...}` for errors -> Update tests to assert the stable envelope.
- FastAPI validation details are richer than the new frontend message -> Keep a readable stable message and stable category; do not model every validation field in COP-117.
- Catching broad exceptions can hide programming errors in development -> Use it only at the API boundary and keep tests focused on expected route behavior.
