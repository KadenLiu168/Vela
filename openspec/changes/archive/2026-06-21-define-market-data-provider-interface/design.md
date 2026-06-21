## Context

Vela already has normalized persistence models for ETF metadata and daily market prices. The next foundation gap is the boundary between external data sources and the core market data workflows.

There is no AkShare integration yet, so this change should define a provider-agnostic contract first. Future ingestion code can adapt provider output into `MarketPrice` rows without making provider implementations depend on SQLAlchemy or database sessions.

## Goals / Non-Goals

**Goals:**
- Define a minimal `MarketDataProvider` interface for ETF daily price fetching.
- Define a normalized daily price value object for provider results.
- Keep the interface independent from AkShare, pandas `DataFrame`, and ORM models.
- Make tests able to use simple fake providers without network access or provider dependencies.

**Non-Goals:**
- Do not implement AkShare or any other real provider.
- Do not persist fetched rows into `MarketPrice`.
- Do not define provider-specific symbol mapping rules.
- Do not add retry, caching, rate limiting, or incremental ingestion orchestration.

## Decisions

1. Define the provider contract in `vela_core`, separate from ORM models.

   Rationale: provider fetching is a core backend boundary but not a persistence concern. Keeping it outside `vela_core.models` avoids coupling external data retrieval to database schema modules.

   Alternative considered: put provider abstractions near `MarketPrice`. That makes the daily price relationship visible, but it mixes external IO contracts with SQLAlchemy model definitions.

2. Return a provider-level daily price DTO instead of `MarketPrice` ORM rows.

   Rationale: provider data is not yet persisted and does not know the internal `etf_id`. A DTO with `symbol`, `trade_date`, OHLC, optional adjusted close, and optional volume is enough for ingestion code to validate and map later.

   Alternative considered: return `MarketPrice` instances. That would reduce mapping code later, but it would force providers to know database identities and ORM classes.

3. Do not expose pandas `DataFrame` in the interface.

   Rationale: AkShare often returns pandas data, but the core provider contract should not depend on one library's table shape. A typed DTO keeps fake providers small and makes the contract easier to test.

   Alternative considered: return `DataFrame` for convenience. That would make the first AkShare adapter thinner but would leak provider formatting and column naming into core workflows.

4. Use a structural typing interface suitable for fake providers.

   Rationale: a `Protocol` lets production adapters and test fakes satisfy the same contract without inheriting from a base class. This keeps the abstraction lightweight and Pythonic.

   Alternative considered: use an abstract base class. That gives nominal registration, but it adds ceremony without clear value for this Phase 1 boundary.

## Risks / Trade-offs

- Provider symbol ambiguity across exchanges -> Keep provider symbol mapping out of this contract and resolve it in a later ingestion/mapping change.
- Provider result DTO may need more fields later -> Start with daily OHLCV and adjusted close because that matches current `MarketPrice`; add fields only when a concrete workflow requires them.
- No real provider implementation in this change -> Validate the boundary with fake-provider tests now, then add AkShare as a separate adapter change.
