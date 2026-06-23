## Context

The core package already contains configuration loading, momentum scoring, defensive fallback selection, and strategy signal persistence. The CLI currently exposes database initialization and market data fetch commands using thin wrappers around core services.

## Goals / Non-Goals

**Goals:**

- Keep CLI orchestration thin and put strategy signal generation in `vela_core`.
- Generate a signal using local database prices only.
- Persist each generation run through the existing signal persistence helper.
- Print a small human-readable summary for local operation.

**Non-Goals:**

- No schema changes, broker integration, web UI, scheduling, or COP-54 behavior.
- No external market data fetch during signal generation.
- No configurable strategy algorithm beyond the existing checked-in strategy config contract.

## Decisions

- Add a `generate_strategy_signal` core service that receives a SQLAlchemy session, signal date, and `StrategyConfig`.
  - Rationale: tests can exercise business logic without invoking argparse or Alembic.
  - Alternative considered: place all logic in `apps/cli`; rejected because CLI tests would need to cover strategy behavior.
- Resolve the ETF universe from active `ETFInfo` rows in the local database.
  - Rationale: acceptance criteria says local market data; `MarketPrice` rows are keyed by persisted ETF ids.
  - Alternative considered: read ETF identities from config and create missing ETFs; rejected because that expands metadata management scope.
- Apply trend filtering before momentum ranking.
  - Rationale: existing strategy config and trend-filtering capability define an eligibility filter used by signal generation.
  - Alternative considered: rank all active ETFs directly; rejected because it would ignore existing strategy rules.
- Persist defensive fallback by looking up the configured defensive asset in `ETFInfo`.
  - Rationale: `StrategySignalPosition` requires an ETF id.
  - Alternative considered: allow position rows without ETF id; rejected because it requires a schema change.

## Risks / Trade-offs

- Missing local ETF metadata or market prices can produce empty or fallback signals -> return clear failed or successful summaries rather than fetching data implicitly.
- Trend filtering and momentum scoring require enough historical rows -> tests cover fallback when eligibility is insufficient.
- The result classification is intentionally simple: selected positions mean `rebalance`, no positions mean `empty`.
