## Context

The Dashboard already triggers market data fetch, signal generation, and backtest run operations through the shared frontend API client. COP-115 added operation pending states and basic failure feedback, but request failures still collapse to normalized kinds such as `http` or `network`, even though `ApiClientError` preserves API response detail text in `message`.

## Goals / Non-Goals

**Goals:**

- Show each critical Dashboard operation failure as a concise summary with the affected operation, readable reason, and suggested next step.
- Use existing API error response parsing from the shared frontend client.
- Keep the implementation local to the web frontend and tests.

**Non-Goals:**

- Change backend error response contracts.
- Add structured error codes, telemetry, or new dependencies.
- Redesign the Dashboard operations panel beyond the error summary content needed for COP-116.

## Decisions

- Represent operation request failures with the existing `ApiClientError` fields plus the operation name.
  - Rationale: `kind`, `status`, and `message` already capture the failure category, HTTP status, and parsed `detail` body without requiring API changes.
  - Alternative considered: add a new API error schema. That would exceed the first-phase frontend scope and require backend coordination.

- Render operation errors as structured feedback content instead of a single string.
  - Rationale: a heading, reason line, and next-step guidance are easier to scan and test than concatenated text.
  - Alternative considered: extend the current `formatOperationError()` string. That is smaller, but it makes reason and guidance less explicit.

- Sanitize technical-looking API detail only enough to avoid it being the only user hint.
  - Rationale: COP-116 does not require classifying every backend exception. Pairing the API detail with stable operation guidance prevents raw database or stack-like text from being the sole visible message while preserving useful local debugging context.

## Risks / Trade-offs

- Backend detail strings can still contain technical wording. -> Mitigate by always showing operation-specific next-step guidance alongside the reason.
- Guidance may be generic for the first phase. -> Keep guidance operation-specific and avoid adding speculative diagnostics that the frontend cannot verify.
