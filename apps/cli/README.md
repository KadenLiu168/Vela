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
