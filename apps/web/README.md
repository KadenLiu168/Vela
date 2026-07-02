# Vela Web

Minimal Vite, React, and TypeScript frontend skeleton for Vela.

## Setup

Install dependencies from the app directory:

```bash
cd apps/web
npm install
```

## Development

Start the development server from the repository root:

```bash
npm --prefix apps/web run dev
```

Equivalent app-local command:

```bash
cd apps/web
npm run dev
```

## Validation

Run frontend tests:

```bash
npm --prefix apps/web run test
```

Run the API client integration test against the local FastAPI service:

```bash
uv run python -m tests.integration_data
uv run vela-api
npm --prefix apps/web run test:integration:api
```

The preparation command resets the default local SQLite database and seeds
deterministic ETF, market price, signal, and backtest rows for API-backed
acceptance checks. Frontend unit tests still use controlled `fetch` mocks for
component states. API integration validation should use the prepared SQLite
state for dashboard, latest signal, and backtest reads; market data fetch
validation may use a controlled provider but must still verify persisted
SQLite rows.

Run lint checks:

```bash
npm --prefix apps/web run lint
```

Run type checking:

```bash
npm --prefix apps/web run typecheck
```

Build the frontend:

```bash
npm --prefix apps/web run build
```

## Structure

```text
src/
├── api/          API client modules
├── components/   Shared React components
├── pages/        Page-level React components
└── test/         Test setup and utilities
```
