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

Start the web frontend development server:

```bash
npm --prefix apps/web run dev
```

Start the local HTTP API service:

```bash
uv run vela-api
```

The API uses the shared local SQLite database URL from `vela_core.database` and
manages request-scoped SQLAlchemy sessions through the core session lifecycle.
It also exposes `GET /api/config` for the current read-only strategy and ETF
pool summary.


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

Next planned work:

- Continue OpenSpec baseline specifications
- Add data provider interface
