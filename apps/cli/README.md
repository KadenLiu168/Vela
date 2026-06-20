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
