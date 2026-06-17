## Context

Vela currently has a minimal core package and no shared logging initialization contract. Phase 1 needs a simple backend-wide baseline so future application entrypoints and jobs can opt into consistent logs without duplicating formatter or level setup.

## Goals / Non-Goals

**Goals:**
- Add a small `vela_core` logging configuration module.
- Provide `setup_logging()` as the single public setup function.
- Allow callers to set a basic log level using either standard logging level names or numeric values.
- Use one consistent format for configured log output.
- Cover the behavior with focused pytest tests and keep ruff clean.

**Non-Goals:**
- No structured JSON logging.
- No file logging, rotating handlers, or external logging integrations.
- No environment-variable settings layer beyond the callable API.
- No changes to application entrypoints unless implementation reveals a direct need.

## Decisions

1. Place the module in `packages/core/src/vela_core/logging.py`.
   - Rationale: logging setup is shared backend infrastructure and belongs in the reusable core package.
   - Alternative considered: a top-level `scripts` or `apps` helper, but that would make reuse by multiple entrypoints awkward.

2. Implement setup with the Python standard library `logging` module.
   - Rationale: the requested behavior is basic level and format configuration, which the standard library already supports.
   - Alternative considered: adding a logging dependency, but that would be unnecessary for the current scope.

3. Use `logging.basicConfig(..., force=True)` in `setup_logging()`.
   - Rationale: tests and repeated setup calls need deterministic behavior, and application entrypoints should be able to establish the configured baseline.
   - Alternative considered: manually managing root handlers, but that adds code without improving the requested behavior.

4. Keep the function API narrow: `setup_logging(level: str | int = logging.INFO) -> None`.
   - Rationale: this supports the required level configuration without introducing speculative knobs.
   - Alternative considered: accepting formatter, handler, or stream parameters, but those are outside the issue.

## Risks / Trade-offs

- `force=True` replaces existing root handlers → acceptable for application-level setup; document by keeping the function as explicit setup rather than implicit import behavior.
- A narrow API may need expansion later → acceptable because future structured logging or handler support can be proposed separately.
- Tests that inspect global logging state can interfere with each other → mitigate by detaching pre-existing root handlers before each logging test so `force=True` does not close them, then closing test-created handlers and restoring the original root logger state afterward.
