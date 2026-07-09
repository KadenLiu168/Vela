# Vela — Architecture Overview

> Derived from the OpenSpec consistency audit (2026-07-09). Component → OpenSpec spec → implementation map. OpenSpec (`openspec/specs/`) is the Single Source of Truth; read it before extending the system.

## Layered data flow

```
CLI / API entrypoints
        ↓
vela_core services
  (provider → fetcher → scoring → signal → backtest)
        ↓
SQLAlchemy models  →  SQLite
```

Dependency direction is correct: entrypoints depend on `vela_core`; `vela_core` never imports entrypoints or Alembic (decoupled per `refactor: decouple core from alembic`). No Controller-direct-to-DB anti-pattern.

## Components

| Component | Responsibility | OpenSpec spec(s) | Implementation |
|---|---|---|---|
| Core business logic | ETF market data, momentum scoring, signal generation, backtesting, portfolio, dashboard aggregation | `market-data`, `market-data-provider`, `momentum-scoring`, `trend-filtering`, `strategy-*`, `backtest-*`, `dashboard-aggregation`, `portfolio-holdings`, `market-price-panel-loading` | `packages/core/src/vela_core/` (30 modules) |
| API service | FastAPI HTTP endpoints | `http-api-service`, `cli-database-initialization` (partial), `local-setup-bootstrap` | `apps/api/src/vela_api/main.py` |
| CLI | Command-line entrypoint | `cli-database-initialization` | `apps/cli/src/vela_cli/main.py` |
| Web frontend | React/TS SPA (Dashboard, backtest list/detail, signal detail, setup, command palette) | `web-frontend-app`, `design-system`, `card-type-scale`, `command-palette`, `detail-page-typography-consistency`, `web-rebalance-frequency-display` | `apps/web/src/` |
| Data layer / migrations | SQLAlchemy models + Alembic | `database-session`, `database-migrations`, `alembic-migration-runner` | `packages/core/.../models/`, `alembic/` |
| Configuration | YAML strategy config + pydantic schema | `application-configuration`, `strategy-configuration` | `config/*.yaml`, `packages/core/.../config.py` |
| Tests | Unit / contract / integration | `test-suite-validation`, `integration-test-data` | `packages/core/tests/`, `apps/*/tests/`, `tests/` |
| Docs | Architecture & acceptance | — | `docs/` |

## Notes

- All `vela_core` modules map to at least one active spec; no orphan modules.
- This file is advisory (hand-derived from the audit), not a living doc — regenerate or correct it if the map drifts.
