## Context

Vela already has a typed ETF pool YAML schema and an `ETFInfo` ORM model, but they are not connected by any setup workflow. Market data fetching and signal generation read active ETFs from `etf_info`, while `/api/config` reads the YAML configuration directly. A new local database can therefore be initialized successfully but still cannot fetch market data because no active ETF rows exist.

## Goals / Non-Goals

**Goals:**

- Provide an explicit, repeatable sync path from the configured ETF pool to `etf_info`.
- Keep synchronization logic in `packages/core` so CLI code remains an entrypoint wrapper.
- Preserve existing market data fetch behavior and make the first-run setup sequence clear.

**Non-Goals:**

- Do not make `fetch-market-data` automatically modify ETF metadata.
- Do not add ETF pool membership tables or named persisted pools.
- Do not delete or deactivate persisted ETFs that are absent from the YAML pool.
- Do not add a database migration.

## Decisions

1. Add a core sync service instead of implementing the mapping in CLI.
   Rationale: `ETFInfo` persistence is core domain behavior and should be reusable by future API or setup workflows. Alternative considered: write rows directly inside `vela_cli.main`; rejected because it would mix application argument handling with persistence rules.

2. Use `(exchange, symbol)` as the ETF identity.
   Rationale: this matches the existing database unique constraint and ETF pool duplicate validation. Alternative considered: use `symbol` only; rejected because the model and config explicitly allow the same symbol on different exchanges.

3. Upsert only fields expressed by the YAML pool: `name`, `currency`, `category`, and `is_active`.
   Rationale: those fields are controlled by the current config schema. Persisted fields such as `issuer`, `inception_date`, and `expense_ratio` are not present in YAML and should not be overwritten.

4. Leave out-of-pool rows untouched.
   Rationale: persisted market prices and strategy records reference ETF ids. Automatically deleting or deactivating rows that are absent from one config file could break historical data workflows. A separate cleanup command can be proposed later if needed.

## Risks / Trade-offs

- A user may expect `fetch-market-data` to work immediately after `init-db` -> CLI docs and output should make `sync-etf-pool` the explicit setup step.
- Out-of-pool rows can remain active -> this preserves safety for historical data, but users must edit existing rows manually until a future cleanup workflow exists.
- Config schema remains minimal -> the sync service cannot populate issuer or expense fields until those become part of ETF pool configuration.
