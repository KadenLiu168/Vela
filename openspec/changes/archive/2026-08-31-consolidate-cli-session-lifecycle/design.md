## Context

See `proposal.md` for motivation. `vela_core.database` already owns engine creation, session-factory creation, and commit/rollback/close behavior. The CLI currently composes those primitives ten times in one module, while the API intentionally retains one application-level factory and opens a managed session per request.

The consolidation must keep non-database configuration and document loading outside the managed-session context, leave the repository-root `vela.db` untouched during validation, and preserve current command contracts and per-invocation engine creation.

## Goals / Non-Goals

**Goals:**

- Give the ten named CLI helpers one private URL-to-managed-session composition boundary.
- Keep `managed_session(session_factory)` as the only transaction-policy implementation.
- Preserve each command-specific operation, session scope, per-invocation engine creation, and intentional error behavior.
- Retain existing regression suites as the primary behavior proof, adding one focused CLI-local test only if a real coverage gap remains.

**Non-Goals:**

- No core or API lifecycle change, public database API, reusable database abstraction module, engine cache, engine reuse, or explicit disposal policy.
- No change to `init-db`, `walk-forward-worker`, pooling, SQLite WAL setup, schema, migrations, ORM models, configuration schemas, CLI interfaces, or domain behavior.
- No duplicate transaction-lifecycle tests in the CLI suite and no ECO-59 work.

## Decisions

1. **Keep one private context-managed helper in `apps/cli/src/vela_cli/main.py`.** The helper accepts `database_url`, calls `create_engine_from_url()`, calls `create_session_factory()`, and delegates its yielded session to `managed_session()`. All affected callers already live in this module, so a new module, `DatabaseManager`, `UnitOfWork`, repository layer, or dependency-injection mechanism would add ownership without another use case.

2. **Delegate transaction policy without wrapping it.** The helper contains no direct `commit()`, `rollback()`, or `close()` calls and does not catch or translate business exceptions. This retains the core boundary's successful commit, failed rollback and re-raise, and all-exit close behavior. Expanding `managed_session()` to accept URLs or adding a core `managed_session_from_url()` was rejected because the gap is CLI composition, not a missing shared capability.

3. **Migrate only the ten named helpers.** Replace their repeated engine/factory/session setup with the private boundary while leaving each business call and return statement intact. `init-db` uses Alembic rather than this session path, and `walk-forward-worker` owns a different long-running lifecycle, so neither belongs in this refactor.

4. **Prepare non-database inputs before entering the private session scope.** Strategy, Walk-forward, application, and ETF session-status loading remains visibly separate from database work and is not moved inside the context merely to reduce lines. Existing tests determine any intentional error-order contract; the implementation must not use this refactor to translate or otherwise redesign errors.

5. **Preserve resource policy by omission.** Every helper invocation still creates one engine and one session factory through the same core primitives. The helper adds no cache, registry, cross-command reuse, pooling arguments, or `engine.dispose()` call, so lifecycle behavior remains equivalent to the current CLI wiring.

## Risks / Trade-offs

- [Risk] The helper accidentally becomes a second transaction-policy owner → Mitigation: its body only composes the three existing core primitives, with lifecycle behavior delegated unchanged to `managed_session()`.
- [Risk] Consolidation widens session scope around file or YAML work → Mitigation: load all non-database inputs before entering the private context and retain focused command regressions.
- [Risk] A named helper, `init-db`, or `walk-forward-worker` is missed or unintentionally included → Mitigation: search the CLI for direct primitive composition and verify the final diff against the explicit ten-function allowlist.
- [Risk] Tests write to the persistent local database → Mitigation: run existing tests with their `tmp_path` databases and do not invoke side-effecting CLI commands against the default URL.

## Migration Plan

Apply the private helper and ten caller substitutions in one local change, run focused core/CLI regressions, then run the full Python gate. No data migration or deployment sequencing is required; rollback is the direct reversal of the CLI-only refactor.
