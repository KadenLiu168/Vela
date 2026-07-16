## Context

The current single-date strategy signal flow has a clear pure core function, `generate_strategy_signal`, that accepts injected inputs and intentionally performs no database queries. That boundary is valuable and should remain intact.

The missing layer is a core application service for the non-pure workflow around that calculation. Today both the FastAPI endpoint and CLI command independently perform the same orchestration: resolve the signal date, query active ETFs, load the price panel, build the defensive ETF lookup, construct a persistence callback, convert generated positions into persistence inputs, and call the pure generation function. This makes API and CLI behavior dependent on duplicated transport-layer implementation details.

Backtest execution already demonstrates the preferred direction: core code owns the session-based orchestration and persistence workflow, while entrypoints load parameters and map output.

## Goals / Non-Goals

**Goals:**

- Move single-date signal generation persistence orchestration into `vela_core`.
- Preserve `generate_strategy_signal` as the pure injected-input calculation entry point.
- Make HTTP and CLI generate-signal paths share one core implementation for active ETF loading, price panel loading, defensive lookup construction, persistence input conversion, and signal persistence.
- Preserve existing user-visible contracts: HTTP response shape, HTTP error shape, CLI arguments, CLI output, persisted schema, and strategy result semantics.
- Add focused core tests for the shared orchestration behavior.

**Non-Goals:**

- Do not change the strategy algorithm, momentum scoring, trend filtering, defensive fallback behavior, or target weight semantics.
- Do not change database schema or add migrations.
- Do not introduce new external dependencies.
- Do not refactor historical backtest signal generation beyond any small helper reuse that is necessary and low-risk.
- Do not change how strategy config YAML is parsed or validated.

## Decisions

### Add a core application service for single-date generation

Create a core function with this shape:

```python
def generate_and_persist_strategy_signal(
    session: Session,
    *,
    config: StrategyConfig,
    signal_date: date | None = None,
) -> GenerateStrategySignalResult:
    ...
```

Rationale:

- The function belongs in core because it coordinates core models, price-panel loading, strategy calculation, and signal persistence.
- Accepting a loaded `StrategyConfig` matches existing core orchestration style such as `run_backtest(session, *, config, ...)`.
- Keeping config loading outside the service lets API and CLI retain responsibility for their own parameter/config source selection.

Alternatives considered:

- `generate_and_persist_signal(session, config_path, signal_date=None)`: rejected because reading config files is an entrypoint concern and would make the core service responsible for filesystem configuration selection.
- Modify `generate_strategy_signal` to accept a session: rejected because the current pure-function boundary is explicit, tested, and useful for deterministic strategy tests.

### Prefer a separate service module over expanding the pure generation module

Implement the orchestration in a module such as `vela_core.strategy_signal_service`, and export the public function from `vela_core.__init__`.

Rationale:

- `strategy_signal_generation.py` currently documents pure, injected-input generation. Adding session-based orchestration there would blur the module’s purpose.
- A service module makes the architectural distinction explicit: generation is pure; service orchestration is impure and persistence-aware.

Alternatives considered:

- Add the service directly to `strategy_signal_generation.py`: acceptable but less clear, because the file already emphasizes zero database access for generation.

### Keep transaction ownership consistent with existing entrypoints

The service should call `persist_strategy_signal` and flush through that helper, then commit after single-date signal generation is persisted, matching the current API and CLI behavior. The surrounding `managed_session` in CLI may still perform a final no-op commit on successful exit.

Rationale:

- Current API and CLI paths explicitly commit inside their persistence callback.
- Preserving commit timing reduces behavior change risk for users who call the endpoint/command and then immediately read latest signals.

Alternative considered:

- Let caller-managed transaction boundaries commit after the service returns: cleaner in isolation, but it changes current behavior and would require reviewing all callers for transaction assumptions.

### Keep API/CLI responsible for transport mapping only

After extraction:

- API should load/obtain config, call the core service, translate `ValueError("No local market prices found")` into HTTP 400, and format the response.
- CLI should parse args, load config by path, open the managed session, call the core service, print the summary, and return the existing status code.

Rationale:

- This keeps transport concerns in `apps/` and business orchestration in `packages/core`.
- It minimizes API/CLI changes and makes future signal workflow changes happen in one place.

## Risks / Trade-offs

- [Risk] Moving persistence orchestration may accidentally change API/CLI behavior. → Mitigation: keep existing API and CLI contract tests passing and add core service tests that assert date resolution, persistence, and missing-market-data behavior.
- [Risk] A new service module may feel like additional indirection for a small workflow. → Mitigation: the extracted code removes duplicated 40-line blocks from two entrypoints and creates a single place for future signal workflow changes.
- [Risk] Commit behavior can be subtle with SQLAlchemy sessions. → Mitigation: preserve the existing explicit commit after persistence and test that persisted signals/positions are visible after generation.
- [Risk] The service could blur pure vs impure strategy boundaries if named poorly. → Mitigation: name it with `and_persist` and keep the pure `generate_strategy_signal` unchanged.

## Migration Plan

1. Add the core service and tests.
2. Export the service from `vela_core.__init__`.
3. Replace duplicated API endpoint orchestration with a call to the service.
4. Replace duplicated CLI wrapper orchestration with a call to the service.
5. Remove now-unused imports from API and CLI modules.
6. Run focused core/API/CLI tests for signal generation.

Rollback is straightforward: revert the API and CLI call sites to their previous inline orchestration and remove the new service/export.

## Open Questions

None. The implementation can proceed with the loaded-config service signature and no user-visible behavior changes.
