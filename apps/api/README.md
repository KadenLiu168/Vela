# Vela API

Minimal FastAPI service skeleton for local Vela frontend calls.

## Development

Start the API service from the repository root:

```bash
uv run vela-api
```

The service binds to `127.0.0.1:8000` by default.

## Health Check

Check the local API health endpoint:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"healthy"}
```

## Database Session

The API app initializes a SQLAlchemy session factory from the shared default
local database URL in `vela_core.database`. Request handlers that need database
access should use the API database session dependency so successful request work
is committed, failed request work is rolled back, and sessions are closed by the
core managed session lifecycle.

## Boundary

The API app is an application entrypoint. Strategy, market data, signal, and
backtest logic must stay in `vela_core`; API routes should wrap existing core
capabilities instead of reimplementing them.
