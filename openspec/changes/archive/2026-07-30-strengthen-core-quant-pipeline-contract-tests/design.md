## Context

Vela's current suite has strong focused coverage for market-data mapping, ETF and calendar synchronization, strategy generation, backtest orchestration, equity calculations, persistence, and API responses. It also has real-strategy backtest integration coverage. The remaining risk is at the seams: no single deterministic test starts from synchronized metadata and calendar rows, persists provider-shaped prices, follows both the live-signal and backtest branches, and reads the resulting state back through core query services.

The current P0 API workflow covers the user-visible sequence, but it hand-seeds ETF and calendar rows, treats natural days as sessions, fetches only one incremental day, and uses price histories that do not meaningfully distinguish ETF rankings. Shared integration data also seeds a legacy backtest `positions_json` shape that differs from the runner's production serializer.

This is a testing-only change. Existing production behavior, caller-managed transactions, strategy formulas, persistence schemas, and API responses are constraints rather than implementation targets.

## Goals / Non-Goals

**Goals:**

- Establish one canonical, deterministic core integration test for the ingestion-to-quant calculation contracts.
- Prove that live signal generation and backtest execution are separate consumers of the same persisted market state, while the backtest uses only its own generated historical signals.
- Exercise real migration, synchronization, mapping, persistence, strategy, backtest, result-query, and Dashboard aggregation code without replacing core calculation functions.
- Make official sessions, ETF behavior, timestamps, adjustment factors, and test configuration deterministic.
- Align shared `positions_json` fixtures with the production serializer.
- Keep the P0 API workflow focused on HTTP delegation, response serialization, persistence readback, and Dashboard linkage.

**Non-Goals:**

- Changing momentum, trend-filtering, rebalance, portfolio, equity, or metric formulas.
- Changing database models, migrations, core or API public contracts, or frontend behavior.
- Converting `positions_json` into a structured API field.
- Accessing Tencent, akshare, or any other network service in tests.
- Adding a subprocess CLI pipeline E2E or changing CLI dependency injection.
- Replacing focused exact-arithmetic tests with broad workflow assertions.

## Decisions

### 1. Use one canonical core contract test, not duplicate full core and API pipelines

The canonical test will directly compose the real core services against one temporary file-backed SQLite database. It will cover Alembic upgrade, ETF pool sync, trading-calendar sync, full market-data fetch, live signal generation, backtest execution, result readback, Dashboard aggregation, and a second real backtest.

A file-backed database is preferred over in-memory SQLite because migration execution and independently created sessions must observe the same persisted state. The canonical database will be created exclusively by `run_alembic_upgrade(...)`, which upgrades to head; the test must not call `Base.metadata.create_all()` or `prepare_sqlite_database()` for that database. It will create the engine and session factory after migration completes, so Alembic is the sole schema source. Existing migration metadata tests remain responsible for proving that Alembic head matches ORM metadata.

Each major stage will consume committed state through a fresh session: ETF pool sync, calendar sync, full fetch, live signal generation, each backtest run, and final readback. Stages whose core service leaves the transaction to its caller will run inside `managed_session`; services that already own persistence behavior will be called unchanged. The test will not add commits inside production functions. This proves the persisted cross-command contract instead of relying on uncommitted rows visible within one ORM session. The API P0 test remains a complementary transport smoke rather than a second copy of every core assertion.

Alternative considered: expand only the API P0 test. Rejected because setup-only core operations do not all have API endpoints, HTTP failure output is less diagnostic, and it would mix transport assertions with detailed domain-contract assertions.

Alternative considered: add both full core and full API pipelines. Rejected because the duplicated setup and computation assertions would increase maintenance without testing a distinct boundary.

### 2. Use a validated test-owned configuration and ETF pool

The canonical workflow will use an explicit validated strategy configuration and matching ETF pool owned by the test. It will include enough risk and defensive assets to exercise the real dual-momentum path. Expected identities and pool membership will derive from this object. The test configuration will use deliberately short, non-zero momentum and moving-average windows and a fixed rebalance frequency so the real algorithm and multiple rebalance dates are exercised without reproducing the production 63/126/120-session fixture.

This keeps the workflow deterministic and prevents legitimate edits to checked-in production configuration from silently changing signal schedules or metrics. Existing configuration tests remain responsible for checked-in YAML correctness.

Alternative considered: load `config/etf_pool.yaml` directly. Rejected because adding or deactivating a production ETF would require unrelated integration-fixture changes and would violate the existing requirement that deterministic workflows inject test-owned configuration.

### 3. Synchronize an official-session calendar through the real adapter boundary

The test will create a `ModuleType("akshare")`, attach `tool_trade_date_hist_sina()` returning a fixed pandas DataFrame, and inject it with `monkeypatch.setitem(sys.modules, "akshare", fake)`. The DataFrame will use ISO-date string cells, complementing the existing focused `date` and `datetime` calendar tests while exercising the production adapter's string parsing path. The test will then call `sync_trading_calendar_to_db`; it will not insert `TradingCalendar` rows directly.

The returned dates will be a fixed ordered set of official sessions containing the strategy lookback and requested backtest range, with no weekends or accidental natural-day assumptions. The test will assert a successful calendar result before the managed session commits.

Market prices will use exactly the required eligible session dates for every active test ETF. This makes missing-price validation part of the exercised contract.

Alternative considered: hand-seed calendar rows. Rejected because it would leave the calendar synchronization-to-backtest seam untested.

### 4. Generate controlled provider rows with distinguishable series

Shared test support will generate deterministic `DailyPrice` rows for every active test ETF. At minimum, the series will distinguish a stronger risk asset, a weaker or flat risk asset, and defensive assets so ranking and selected identities are meaningful. One known-unselected ETF series will carry the same non-unit adjustment factor on every date. A constant factor survives mapping and database quantization but cancels from adjusted-price return ratios, so the ranking remains readable.

The generator will be formulaic and session-index based; it will not use randomness, current dates, or copied historical market data. `ControlledMarketDataProvider` will record every call as `(symbol, start_date, end_date)` and return only rows within the requested inclusive bounds. P0 incremental fetch tests will fix `market_data_fetcher._today()` so the recorded end date is deterministic. Assertions will verify raw stored `close_price` and `factor_hfq` before signal generation, then selected identities, rank/weight invariants, and metric/readback consistency. Exact financial metric goldens remain in focused tests.

### 5. Treat live and backtest signals as sibling branches

The canonical workflow will first generate and persist a live/manual signal from the fetched state. It will then call `run_backtest`, which must generate and link its own `source="backtest"` historical signals. Assertions will prove that the pre-existing manual signal is not linked to or consumed by the run.

The second real backtest will produce a disjoint set of linked signal IDs. The first run's signals, curve, metrics, and snapshot must remain unchanged. Because both runs use the same persisted price panel, their complete `data_snapshot_json` values, including `data_checksum`, must be equal. Input-mutation checksum behavior remains covered by the focused snapshot tests and will not require a third canonical run.

This encodes the actual architecture and avoids the incorrect assumption that `generate-signal` is a direct input to `run-backtest`.

### 6. Normalize shared position fixtures at their source

The shared equity-curve fixture will serialize positions using the production keys `etf_id`, `target_weight`, and `actual_weight`, with decimal values represented as strings. Tests that intentionally exercise arbitrary opaque text may keep local fixtures, but shared workflow data must model the production contract.

The fixture change does not introduce stricter database validation and does not change the API payload; it only removes misleading shared test data.

### 7. Keep the P0 API workflow thin but representative

Before changing the P0 workflow, implementation will inventory every existing endpoint and assertion as one of: retain as unique transport/readback evidence, rewrite as a derived invariant, or remove because focused/canonical coverage proves the same contract. The P0 workflow will continue to call the real fetch, signal-generation, backtest, detail, latest-signal, and Dashboard endpoints. It will inject a validated short-window test-owned strategy configuration and use shared distinguishable price support.

Implementation inventory:

| Existing workflow evidence | Classification | Result |
|---|---|---|
| Initial and refreshed Dashboard reads | retain | Verify pre-fetch state plus fetch, latest-signal, and recent-run linkage. |
| Incremental fetch HTTP response and provider ordering | rewrite as derived invariant | Retain the response contract; use test-owned pool size and fixed `(symbol, start_date, end_date)` tuples. |
| Signal generation and pre-backtest latest-signal response | retain | Verify manual identity, rank, weight, direct readback, and provenance. |
| Backtest submission and detail response | rewrite as derived invariant | Derive session and signal counts from controlled sessions and linked detail collections. |
| Post-backtest Dashboard latest signal | retain | Compare against the production latest-signal endpoint rather than assuming manual signals remain latest. |
| Placeholder `backend_gaps_or_field_mismatches` assertion | remove as duplicated | It adds no HTTP, persistence, or calculation evidence. |

Its assertions will focus on:

- HTTP success and stable response fields;
- persisted IDs and values matching follow-up API reads;
- serialized signal position identities, ranks, and weights;
- production-shaped equity-curve `positions_json`;
- Dashboard linkage to the generated fetch, the latest successful signal under production ordering, and the recent run.

Hardcoded calendar-derived values such as `trading_day_count == 10` will become invariants derived from the controlled official sessions and the returned equity-curve length. Signal counts will be checked against linked/detail collections rather than weakened to existence-only assertions. Provider request ordering will be retained and expanded to include fixed start/end bounds.

The Dashboard assertion will not assume that the earlier manual signal remains latest after backtest execution: production chooses the latest successful signal by `generated_at` then id, so a backtest-owned signal may be latest. The manual signal will instead be verified through its direct API/readback and unlinked provenance. The P0 test will not duplicate exact financial arithmetic, migration metadata comparison, synchronization edge cases, or the canonical test's complete rerun proof.

## Risks / Trade-offs

- [Risk] The canonical test spans several services, so a failure may have a larger search area than a focused unit test. → Mitigation: keep the workflow as one canonical scenario with stage-specific assertions and retain all existing focused tests.
- [Risk] Even a real dual-momentum workflow can become slow if it copies production windows. → Mitigation: use short, non-zero test-owned windows and a compact fixed official-session list; keep the test in the default pytest suite without introducing a new marker policy.
- [Risk] A varying non-unit factor can make intended rankings hard to reason about. → Mitigation: use one constant non-unit factor on a known-unselected series and assert raw mapped values before signal generation.
- [Risk] Shared fixture normalization can change API/frontend fixture expectations that were relying on legacy sample text. → Mitigation: update only tests using the shared helper and retain local opaque-text tests when their subject is pass-through behavior.
- [Risk] Making the P0 test thinner could accidentally remove unique HTTP coverage or assert the wrong latest signal after a backtest. → Mitigation: inventory every endpoint/assertion first, preserve unique transport and read-after-write evidence, and derive Dashboard latest-signal expectations from production ordering.
