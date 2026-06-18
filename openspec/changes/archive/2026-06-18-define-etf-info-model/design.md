## Context

Vela currently has a small SQLAlchemy session foundation in `vela_core.database`, but no declarative ORM base, no models, and no Alembic migration setup. The next persistence step is to define ETF metadata identity so future market data and strategy workflows can refer to ETFs consistently.

The model must support international markets. Ticker symbols are not globally unique, so ETF identity cannot rely on `symbol` alone.

## Goals / Non-Goals

**Goals:**

- Define a typed SQLAlchemy ORM base that exposes `Base.metadata`.
- Define an `ETFInfo` ORM model for core ETF metadata.
- Use `exchange` and `symbol` together as the ETF identity uniqueness boundary.
- Add practical indexes for symbol lookup, exchange filtering, and active ETF filtering.
- Add Alembic configuration that can discover the model metadata for autogeneration.
- Keep the implementation focused and testable with SQLite.

**Non-Goals:**

- Add repository classes or service APIs for ETF metadata.
- Add ETF import, normalization, or data provider integration.
- Add provider-specific symbol mapping.
- Add market price, NAV, holdings, or corporate action tables.
- Define production database deployment settings.

## Decisions

1. Add models under a `vela_core.models` package.

   Rationale: ORM models are a separate concern from session lifecycle helpers. A models package gives Alembic and future code one predictable import location without expanding `vela_core.database` into a mixed session/model module.

   Alternative considered: define `ETFInfo` in `vela_core.database`. This is smaller initially, but mixes session factories with domain tables and becomes harder to grow once market data models are added.

2. Use SQLAlchemy 2.0 typed declarative mappings.

   Rationale: The project already values typed public APIs. `DeclarativeBase`, `Mapped`, and `mapped_column` keep ORM definitions explicit and compatible with static checks.

   Alternative considered: classic `Column` declarations. They work, but provide weaker typing and do not match modern SQLAlchemy style.

3. Model ETF identity as `UNIQUE(exchange, symbol)`.

   Rationale: International markets can reuse ticker symbols. `exchange + symbol` is the smallest stable identity boundary for exchange-listed ETFs without introducing provider-specific concepts too early.

   Alternative considered: make `symbol` globally unique. This is simpler, but blocks international markets and can create false conflicts.

   Alternative considered: include `country` in the unique constraint. Country is useful metadata, but exchange is closer to the listed security identity and avoids ambiguous country-level markets.

4. Keep provider-specific identifiers out of this model.

   Rationale: Provider symbols and external IDs differ by data source and are better represented by a later mapping table once provider integration exists.

   Alternative considered: add `provider` and `provider_symbol` now. That anticipates future ingestion work, but adds fields whose semantics are not yet defined.

5. Add Alembic as the migration entrypoint for ORM metadata discovery.

   Rationale: The acceptance criteria require Alembic migration recognition. That needs more than a model file: Alembic must import the model registry and assign `target_metadata = Base.metadata`.

   Alternative considered: rely only on tests that call `Base.metadata.create_all()`. That proves SQLAlchemy can create tables, but does not prove Alembic can autogenerate migrations.

## Risks / Trade-offs

- Exchange code semantics can vary by provider -> normalize only the database identity field name now, and defer provider-specific mapping.
- SQLite has limited type enforcement compared with production databases -> test metadata, constraints, and indexes directly rather than relying only on SQLite runtime behavior.
- Alembic setup adds configuration surface area -> keep the initial migration environment minimal and focused on metadata discovery.
- `exchange + symbol` might not identify every future instrument class -> acceptable for ETF metadata now; revisit only if Vela adds cross-listings or provider-specific instruments.

## Migration Plan

- Add Alembic configuration and a migration environment that imports `ETFInfo` before exposing `Base.metadata`.
- Add an initial Alembic revision that creates the ETF metadata table with constraints and indexes.
- Verify autogenerate can compare metadata without missing `ETFInfo`.
- Rollback is the reverse migration dropping the ETF metadata table and indexes.

## Open Questions

- Exact exchange code normalization can be refined when the first data provider integration is designed.
- Whether `country` should be included as optional metadata depends on the target ETF universe and can be added later without changing the identity constraint.
