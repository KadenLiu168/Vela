# Vela

Vela is a personal ETF rotation system focused on strategy research, signal generation, and historical backtesting.

## Phase 1 Goal

The first phase focuses on building the core backend foundation.

Phase 1 includes:

- Monorepo project structure
- Python 3.11+ environment with uv
- Project dependency management with pyproject.toml
- pytest test framework
- Ruff linting and formatting
- Basic logging configuration
- OpenSpec-based specification workflow
- Core backend foundations for future ETF metadata, market data, strategy signals, and backtesting

## Tech Stack

- Python 3.11+
- uv
- pytest
- Ruff
- SQLAlchemy
- pandas
- pydantic
- Vite, React, TypeScript, and npm for the web frontend skeleton
- OpenSpec

## Repository Structure

```text
apps/       Application entrypoints, such as future API and CLI apps
packages/   Reusable business packages
openspec/   Project specifications and change proposals
scripts/    Development and automation scripts
tests/      Repository-level integration tests
docs/       Architecture and design documents
```

Current core package:

```text
packages/core/
├── src/
│   └── vela_core/
│       ├── __init__.py
│       ├── database.py
│       ├── logging.py
│       └── models/
└── tests/
    ├── test_database.py
    ├── test_logging.py
    └── test_smoke.py
```

Current web app skeleton:

```text
apps/web/
├── src/
│   ├── api/
│   ├── components/
│   ├── pages/
│   └── test/
└── package.json
```

Current API app skeleton:

```text
apps/api/
├── src/
│   └── vela_api/
└── tests/
```

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

SQLite is the supported local development workflow for Phase 1. The migration
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
## Phase 1 Scope

Phase 1 focuses on the backend foundation and does not yet include:

- Production data ingestion
- Real ETF strategy logic
- Historical backtest engine
- API service
- Complete business Web UI beyond the current frontend skeleton
- Deployment pipeline

These capabilities will be added in later phases.

## Current Status

Completed:

- Initialized monorepo structure
- Configured uv Python environment
- Configured project dependencies
- Configured pytest
- Configured Ruff
- Added basic logging configuration
- Added SQLAlchemy database session helpers
- Added SQLAlchemy ORM models for ETF metadata, market prices, data fetch logs, strategy signals, and backtest results
- Configured Alembic migrations for local SQLite development
- Added `scripts/dev.sh` to orchestrate the full local stack (backend +
  frontend together) with stale-process cleanup and two-phase shutdown

Next planned work:

- Continue OpenSpec baseline specifications
- Add data provider interface
