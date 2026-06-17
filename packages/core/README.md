# Vela Core

`vela_core` is the core backend package for Vela.

It will contain the shared backend capabilities used by future API, CLI, data ingestion, strategy, and backtesting components.

## Current Responsibilities

At the current stage, this package provides:

- Package skeleton
- Basic version marker
- Basic logging configuration
- Unit tests for package import and logging setup

## Planned Responsibilities

Future responsibilities include:

- Application configuration
- Database session management
- SQLAlchemy ORM models
- ETF metadata management
- Market data storage and query services
- Data provider interfaces
- Strategy signal generation
- Historical backtesting foundation

## Package Layout

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

## Run Tests

From the repository root:

```bash
uv run pytest packages/core/tests
```

Or run all tests:

```bash
uv run pytest
```

## Code Quality

From the repository root:

```bash
uv run ruff check .
uv run ruff format .
```
