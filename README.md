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
│       └── logging.py
└── tests/
    ├── test_smoke.py
    └── test_logging.py
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
- Web UI
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

Next planned work:

- Continue OpenSpec baseline specifications
- Add database and ORM foundation
- Add ETF metadata model
- Add market price model
- Add data provider interface
