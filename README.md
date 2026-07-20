# Vela

Vela is a personal ETF rotation system focused on strategy research, signal generation, and historical backtesting.

## Current State

Vela is a working local MVP for personal ETF rotation research. A CLI and a
FastAPI service drive a dual-momentum strategy and a backtest engine over a real
market-data pipeline, with a React research frontend on top. All core
capabilities are implemented and covered by tests. The system runs locally
against SQLite and is not deployed.

Current capabilities:
- ETF universe management (sync from `config/etf_pool.yaml`)
- Market data fetching & normalization (Tencent + JoinQuant providers; full + incremental; gap detection)
- Market price storage & querying (SQLAlchemy + Alembic on SQLite)
- Dual-momentum signal generation (momentum scoring + trend filter + defense fallback; no look-ahead bias)
- Historical backtesting (total & annualized return, max drawdown, volatility, Sharpe ratio; transaction cost applied)
- FastAPI HTTP service (14 endpoints) + React web UI (6 pages, command palette, SVG charts)
- Trading-calendar sync, data-quality checks, CLI report export

## Tech Stack

Backend:
- Python 3.11+ / uv
- FastAPI + uvicorn
- SQLAlchemy + Alembic
- pandas / pydantic / pydantic-settings
- akshare / tenacity (Tencent data provider); jqdatasdk optional (JoinQuant)

Frontend (apps/web):
- React 19 + Vite + TypeScript + npm
- vitest (unit), Ladle (component previews), eslint, stylelint

Tooling:
- pytest, Ruff, mypy, pre-commit
- OpenSpec for specification-driven development

## Repository Structure

```text
apps/         Application entrypoints (api, cli, web)
packages/     Reusable business packages
openspec/     Project specifications and change proposals
scripts/      Development and automation scripts
tests/        Repository-level integration tests
docs/         Architecture and design documents
```

Core backend package (`packages/core/src/vela_core/`): ORM models, data
providers, momentum scoring, trend filter, signal generation, backtest engine,
trading calendar, data quality, CLI/API service helpers.

Web application (`apps/web/`): React 19 SPA - Dashboard, Signal list/detail,
Backtest list/detail, ETF detail pages, command palette, SVG charts.

API service (`apps/api/src/vela_api/`): FastAPI app with 14 endpoints.

CLI (`apps/cli/src/vela_cli/`): 8 subcommands (init-db, fetch-market-data,
sync-etf-pool, sync-trading-calendar, generate-signal, run-backtest, export
*-report).

## Development Setup

Install dependencies:

```bash
uv sync
```

Check Python version:

```bash
uv run python --version
```

The project expects Python 3.11 or later.

## Common Commands

Run tests:

```bash
uv run pytest
```

Run Ruff lint checks:

```bash
uv run ruff check .
```

Automatically fix lint issues when possible:

```bash
uv run ruff check . --fix
```

Format code:

```bash
uv run ruff format .
```

Check formatting without changing files:

```bash
uv run ruff format --check .
```

Run the canonical local quality gate that mirrors CI:

```bash
uv sync --group dev
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy --config-file pyproject.toml
uv run --no-sync pytest
npm --prefix apps/web ci
npm --prefix apps/web run lint
npm --prefix apps/web run lint:css
npm --prefix apps/web run typecheck
npm --prefix apps/web run test
npm --prefix apps/web run build
```

Initialize or upgrade the local SQLite database to the current migration head:

```bash
uv run alembic upgrade head
```

Reset the local development database from scratch:

```bash
rm -f vela.db && uv run alembic upgrade head
```

Sync the configured ETF pool into the local database:

```bash
uv run vela sync-etf-pool
```

Fetch full daily market data for active ETFs:

```bash
uv run vela fetch-market-data
```

Or fetch only data newer than the latest local market price date:

```bash
uv run vela fetch-market-data --incremental
```

Sync the trading calendar (exchange sessions / trading days):

```bash
uv run vela sync-trading-calendar
```

Generate a strategy signal for a given date (defaults to the latest trading day):

```bash
uv run vela generate-signal
```

Run a backtest over the signal history:

```bash
uv run vela run-backtest
uv run vela run-backtest --strict-data-quality --max-gap-days 5
```

Export the latest signal or a backtest run as a readable report:

```bash
uv run vela export-signal-report
uv run vela export-backtest-report --run-id <id>
```

## Local Development

### Start the full local stack

The canonical way to run the backend and the web frontend together is
`scripts/dev.sh`. It starts `uv run vela-api` (FastAPI on port 8000) and
`npm --prefix apps/web run dev` (Vite on port 5173) in a single terminal
with `[vela-api]` / `[vela-web]` line-prefixed output, and cleans up any
stale Vela-owned processes on those ports before launching.

From the repository root:

```bash
./scripts/dev.sh
```

What you get:

- Both services run in the background. Their logs interleave in your
  terminal; every line is prefixed with the service name so you can tell
  them apart at a glance.
- The FastAPI backend is reachable at `http://127.0.0.1:8000`.
- The Vite dev server is reachable at `http://localhost:5173` and
  proxies `/api/*` to the backend.
- The script refuses to start if `uv`, `npm`, `lsof`, or `ps` is missing
  on `PATH` (clear error message, no half-started state).
- If a previous `uv run vela-api` left an orphan on port 8000, the
  preflight cleanup kills it before launching the fresh backend. You
  will not see `Address already in use` again.

To stop both services, press `Ctrl+C` in the terminal where `dev.sh` is
running. The script sends `SIGTERM` to both children, waits up to 5
seconds, then `SIGKILL`s any survivors. The pidfiles in
`/tmp/vela-api.pid` and `/tmp/vela-web.pid` are removed on the way out.

If you started `dev.sh` in the background from another shell, stop it
with:

```bash
kill -TERM $(cat /tmp/vela-api.pid) 2>/dev/null; pkill -TERM -f 'scripts/dev.sh'
```

The full kill-scope and shutdown contract is documented in
`scripts/README.md` and in the OpenSpec capability
`openspec/specs/dev-orchestration-script/spec.md`.

### Run a single service in isolation

Use these only when you need to start a single service in isolation —
e.g., when running the API integration test against a remote backend.
The `dev.sh` script is the recommended path for normal iteration.

Start the web frontend development server on its own:

```bash
npm --prefix apps/web run dev
```

Start the local HTTP API service on its own:

```bash
uv run vela-api
```

The API uses the shared local SQLite database URL from `vela_core.database`
and manages request-scoped SQLAlchemy sessions through the core session
lifecycle. It also exposes `GET /api/config` for the current read-only
strategy and ETF pool summary.

## Database Migrations

Vela uses Alembic for database schema migrations. The default local development
database is SQLite at `vela.db`, configured in `alembic.ini`.

Create or upgrade the local SQLite database to the current migration head:

```bash
uv run alembic upgrade head
```

Check the current migration head:

```bash
uv run alembic current
```

Generate SQL for review without applying migrations:

```bash
uv run alembic upgrade head --sql
```

Reset the local development database from scratch:

```bash
rm -f vela.db
uv run alembic upgrade head
```

SQLite is the supported local development workflow. The migration
environment imports the SQLAlchemy ORM models and exposes `Base.metadata` so
future revisions can be generated from model metadata.

## OpenSpec Workflow

Vela uses OpenSpec to guide development.

Long-lived project specifications live under:

```text
openspec/specs/
```

Future changes should be created under:

```text
openspec/changes/<change-id>/
```

A typical change may include:

```text
proposal.md
tasks.md
design.md
specs/
```

The goal is to keep implementation work aligned with written specifications and small incremental changes.

## Local Quality Feedback

Install the local hook runner once per clone:

```bash
uv sync --group dev
uv run pre-commit install
```

Run the configured hooks manually when needed:

```bash
uv run pre-commit run --all-files
```

The repository's GitHub branch protection or ruleset for `main` must require the Python and frontend CI jobs before the quality gate is a real merge gate.
## Out of Scope (Project-wide)

The following are explicitly outside Vela's mandate:
- Real-time trading / broker integration / automated order execution
- Production deployment (currently local-only: SQLite + 127.0.0.1)
- Complex portfolio optimization

## Current Status

Implemented (code complete + tested):
- Monorepo, uv environment, pytest, Ruff, mypy, pre-commit
- SQLAlchemy models + Alembic (10 revisions, 8 business tables)
- CLI data pipeline: `sync-etf-pool`, `fetch-market-data`, `sync-trading-calendar`,
  `generate-signal`, `run-backtest`, report export
- FastAPI service with 14 endpoints + structured error envelope
- React research frontend (Dashboard / Signals / Backtests / ETF detail + command palette + SVG charts)
- Dual-momentum strategy v1, backtest engine, Tencent + JoinQuant data providers,
  trading calendar, data-quality checks

Validation status (verified against local `vela.db`):
- Data layer IS exercised on real data: `market_price` 29,311 rows, `etf_info` 11 rows.
- NOT yet generated: `strategy_signal`, `backtest_run`, `backtest_equity_curve`,
  `trading_calendar` are all 0 rows - signal/backtest/calendar end-to-end run pending.
- Deployment: local-only, not deployed.

Next planned work:
- Run the signal -> backtest -> calendar closed loop on real data and export a readable report
- Wire business logging (replace `logging.py` basicConfig stub)
- Add an ETF list page + `/api/etfs` endpoint
- Reconcile remaining OpenSpec spec Purpose fields
