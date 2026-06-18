## 1. Tests

- [x] 1.1 Add tests that inspect `ETFInfo.__table__` and verify all required ETF metadata columns exist.
- [x] 1.2 Add tests that verify `exchange` and `symbol` are enforced as a composite unique constraint.
- [x] 1.3 Add tests that verify rows with the same `symbol` on different `exchange` values can coexist.
- [x] 1.4 Add tests that verify duplicate `exchange` and `symbol` values are rejected.
- [x] 1.5 Add tests that verify indexes exist for `symbol`, `exchange`, and `is_active`.
- [x] 1.6 Add tests that verify Alembic target metadata includes the ETF metadata table.

## 2. ORM Implementation

- [x] 2.1 Add a `vela_core.models` package with a typed SQLAlchemy declarative `Base`.
- [x] 2.2 Add the `ETFInfo` ORM model with core metadata columns.
- [x] 2.3 Add the `UNIQUE(exchange, symbol)` constraint.
- [x] 2.4 Add indexes for `symbol`, `exchange`, and `is_active`.
- [x] 2.5 Ensure model modules are imported in a predictable place so `Base.metadata` contains `ETFInfo`.

## 3. Alembic Implementation

- [x] 3.1 Add Alembic dependency and minimal configuration.
- [x] 3.2 Add an Alembic migration environment that sets `target_metadata` to `Base.metadata`.
- [x] 3.3 Add an initial revision that creates the ETF metadata table, constraints, and indexes.

## 4. Verification

- [x] 4.1 Run `uv run pytest packages/core/tests`.
- [x] 4.2 Run `uv run ruff check packages/core/src packages/core/tests`.
- [x] 4.3 Run `uv run mypy packages/core/src packages/core/tests`.
- [x] 4.4 Run an Alembic metadata or autogenerate check that confirms the ETF table is discoverable.
