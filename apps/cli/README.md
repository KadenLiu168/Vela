# Vela CLI

The Vela CLI provides local development commands.

Initialize the local SQLite database:

```bash
uv run vela init-db
```

By default, this initializes `sqlite+pysqlite:///vela.db` using the project's Alembic
migrations. To target a different SQLite file:

```bash
uv run vela init-db --database-url sqlite+pysqlite:////tmp/vela.db
```

Fetch full daily market data for active ETFs:

```bash
uv run vela fetch-market-data
```

Fetch only daily market data newer than the latest local market price date:

```bash
uv run vela fetch-market-data --incremental
```

Incremental mode uses the maximum local `market_price.trade_date` as its baseline and
requests provider data starting from the next calendar day. It fails instead of falling
back to a full fetch when no local market prices exist.

Sync the configured ETF pool into the local database:

```bash
uv run vela sync-etf-pool
```

The default pool comes from `config/strategy_v1.yaml`. To override the strategy
or ETF pool YAML path:

```bash
uv run vela sync-etf-pool --strategy-config config/etf_pool.yaml
```

Generate and persist the latest strategy signal based on the latest local market
price date:

```bash
uv run vela generate-signal
```

The signal date defaults to the maximum local `market_price.trade_date`. To
generate for a specific date:

```bash
uv run vela generate-signal --signal-date 2026-07-04
```

Export the latest persisted strategy signal report to stdout:

```bash
uv run vela export-signal-report
```

Optionally write the report to a file:

```bash
uv run vela export-signal-report --output reports/signal.md
```

Run a historical backtest between two dates and persist the result:

```bash
uv run vela run-backtest --start-date 2025-01-01 --end-date 2025-12-31
```

Export a persisted backtest report by run id to stdout:

```bash
uv run vela export-backtest-report --run-id 1
```

Optionally write the report to a file:

```bash
uv run vela export-backtest-report --run-id 1 --output reports/backtest.md
```
