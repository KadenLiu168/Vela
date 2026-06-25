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

## Boundary

The API app is an application entrypoint. Strategy, market data, signal, and
backtest logic must stay in `vela_core`; API routes should wrap existing core
capabilities instead of reimplementing them.
