## Why

AkShare and Tencent, the two existing market data providers, are library-homogeneous: both delegate to the `akshare` package (`fund_etf_hist_em` and `stock_zh_a_hist_tx`). They do not actually exercise the `MarketDataProvider` abstraction against an independent library. The spec already mandates "Provider implementation independence" (`openspec/specs/market-data-provider/spec.md`), but nothing in the codebase has ever proven it against a non-akshare backend. JoinQuant (`jqdatasdk`) is the first genuinely library-independent data source, so adding it both validates the abstraction and unblocks Phase 3 multi-source comparison.

## What Changes

- Add `JoinQuantMarketDataProvider`, a thin `BaseMarketDataProvider` subclass (~45 lines) that fills the existing hook contract (`name`, `_source_label`, `_column_map`, `_fetch_rows` with `@retry`, `_format_request_symbol`, and an `__init__` override). No base-class changes.
- Handle three real differences from AkShare/Tencent inside the subclass, not the base:
  - Trade date lives in the DataFrame index, not a column → `_fetch_rows` sets `df.index.name = "trade_date"` then `reset_index()` so the base `_normalize_rows` column check passes.
  - Symbol format uses the `XSHG`/`XSHE` suffix (e.g. `510300.XSHG`) instead of the `sh`/`sz` prefix → custom `_format_request_symbol`.
  - `jqdatasdk.auth(username, password)` is required before any fetch → `__init__` reads credentials from environment variables (`JQ_USERNAME`, `JQ_PASSWORD`) via `python-dotenv`, authenticates lazily and exactly once per process (module-level flag). Credentials are never hardcoded and never read from the git-tracked `config/*.yaml`.
- Declare `jqdatasdk` as an optional dependency under `[project.optional-dependencies]` (`joinquant` extra). Contributors who do not opt in are unaffected.
- Add `.env.example` (key names only, no values) so the required environment variables are documented; actual credentials live in `.env`, which `.gitignore` already ignores.
- Add unit tests using a fake `jqdatasdk` module (mirroring the existing `FakeAkShareModule` pattern) covering normalization, symbol formatting, `reset_index`, error wrapping, ordering, and the auth-once invariant.
- Add a credentials-gated integration smoke test (`@pytest.mark.skipif` when `JQ_USERNAME`/`JQ_PASSWORD` are absent) that fetches a real `510300.XSHG` daily bar and writes it through the persistence layer, verifying jqdatasdk's real output contract (date format, index name, auth flow).
- Add a new "JoinQuant ETF daily price provider" requirement with scenarios to `market-data-provider`. Default provider stays Tencent; CLI and API default instantiation paths are NOT touched, and no `build_provider` factory is introduced (deferred to Phase 3 when multi-source has a real consumer).
- Extend the existing contract-independence test to also assert `market_data_provider.py` contains neither `jqdatasdk` nor `joinquant`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `market-data-provider`: Add a "JoinQuant ETF daily price provider" requirement with scenarios covering fetch delegation, `XSHG`/`XSHE` symbol mapping, date index handling, unadjusted prices, normalization, error propagation, validation, and credentials-via-environment with lazy single auth. The default-provider-is-Tencent requirement is unchanged.

## Impact

- **Code**: new `packages/core/src/vela_core/joinquant_market_data_provider.py`; one export line in `packages/core/src/vela_core/__init__.py`. No changes to `base_market_data_provider.py`, `market_data_provider.py`, the CLI, the API, the fetcher, or the calculation layer.
- **Dependencies**: `pyproject.toml` gains `[project.optional-dependencies]` `joinquant = ["jqdatasdk"]`. This is the project's first PEP 621 extras entry alongside the existing PEP 735 `[dependency-groups]`; CI must decide whether to run a matrix with the extra installed.
- **Configuration**: `.env.example` added (committed); real credentials in `.env` (gitignored, already covered by `.gitignore`). `AppConfig` is NOT modified.
- **Tests**: fake-module unit tests (no credentials, no network) plus a gated integration smoke test (requires real credentials, skipped otherwise). Existing AkShare/Tencent tests, CLI/API default-path tests, and the contract-independence test remain green.
- **Specs**: `openspec/specs/market-data-provider/spec.md` gains the JoinQuant requirement and scenarios.
- **Out of scope** (deferred): `build_provider(name)` factory, CLI/API default-path refactor, multi-source comparison harness, formal `JoinQuantSettings` via `pydantic-settings.BaseSettings`.
