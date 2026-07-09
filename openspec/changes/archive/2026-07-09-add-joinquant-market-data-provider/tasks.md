## 1. Optional dependency and credential scaffold

- [x] 1.1 Add `[project.optional-dependencies]` with `joinquant = ["jqdatasdk"]` to `pyproject.toml`
- [x] 1.2 Create `.env.example` with `JQ_USERNAME=` and `JQ_PASSWORD=` (key names only, no values)
- [x] 1.3 Verify `.gitignore` already ignores `.env` / `.env.*` — required adding `!.env.example` negation so the template is committable (the `.env.*` pattern was swallowing `.env.example`)
- [x] 1.4 Verify `uv sync` succeeds without the `joinquant` extra and that `jqdatasdk` is absent from the default install — confirmed via `uv.lock`: `jqdatasdk` is locked under `[package.optional-dependencies] joinquant` with marker `extra == 'joinquant'`, not in default `dependencies`

## 2. JoinQuant provider implementation

- [x] 2.1 Create `packages/core/src/vela_core/joinquant_market_data_provider.py` defining `JoinQuantMarketDataProvider(BaseMarketDataProvider)`
- [x] 2.2 Set class attributes `name = "joinquant"`, `_source_label = "joinquant"`, and a `_column_map` mapping `trade_date`/`open`/`high`/`low`/`close`/`volume` to jqdatasdk's column names
- [x] 2.3 Implement `_format_request_symbol` appending `XSHE` for symbols starting with `15` and `XSHG` otherwise
- [x] 2.4 Override `__init__`: call `dotenv.load_dotenv()`, read `JQ_USERNAME`/`JQ_PASSWORD` from `os.environ`, raise `MarketDataProviderError` if missing, lazy-import `jqdatasdk` via `import_module`, authenticate exactly once via a module-level flag, then call `super().__init__(source)` with the imported module (or an injected source)
- [x] 2.5 Implement `_fetch_rows` with `@retry(...)`: call the jqdatasdk fetch function, then set `df.index.name = "trade_date"` and `df = df.reset_index()` before returning
- [x] 2.6 Ensure NO top-level `import jqdatasdk` in the module (lazy `import_module` inside `__init__` only) — verified by `test_import_vela_core_does_not_require_jqdatasdk`
- [x] 2.7 Export `JoinQuantMarketDataProvider` from `packages/core/src/vela_core/__init__.py` and add it to `__all__`

## 3. Fake-module unit tests (no credentials, no network)

- [x] 3.1 Create `packages/core/tests/test_joinquant_market_data_provider.py`
- [x] 3.2 Add a `FakeJoinQuantModule` (and failing/flaky variants) mirroring the existing fake pattern, returning DataFrames with the date in the index
- [x] 3.3 Test normalization of OHLCV fields including the `reset_index` path (date starts as index, ends as `trade_date` column)
- [x] 3.4 Test `XSHG`/`XSHE` symbol suffix mapping
- [x] 3.5 Test date-bounds are forwarded to jqdatasdk (converted to `YYYY-MM-DD`)
- [x] 3.6 Test empty result returns an empty sequence
- [x] 3.7 Test source-call failure is wrapped in `MarketDataProviderError` with context, and retries before raising
- [x] 3.8 Test row normalization/validation failures are wrapped without retry
- [x] 3.9 Test ascending-by-trade-date ordering regardless of source row order
- [x] 3.10 Test missing-credentials raises `MarketDataProviderError` (constructor path), using a fake source so no real auth runs
- [x] 3.11 Test the lazy single-auth invariant: constructing two instances with a fake source calls auth at most once

## 4. Contract independence and import guards

- [x] 4.1 Extend `test_provider_contract_module_remains_source_library_independent` to also assert `market_data_provider.py` contains neither `jqdatasdk` nor `joinquant`
- [x] 4.2 Add a test asserting `import vela_core` succeeds and does not load `jqdatasdk` when the extra is not used
- [x] 4.3 Add a test that constructing `JoinQuantMarketDataProvider` without the extra installed (monkeypatched `import_module`) raises a clear `MarketDataProviderError`

## 5. Gated integration smoke test (Phase B — requires credentials)

- [x] 5.1 Create `tests/test_joinquant_integration.py` with `@pytest.mark.skipif` on `JQ_USERNAME`/`JQ_PASSWORD`
- [x] 5.2 Test fetching a real `510300.XSHG` daily bar over a recent date range through `JoinQuantMarketDataProvider`
- [x] 5.3 Assert the returned `DailyPrice` values are valid (positive OHLC, consistent OHLC relationship, parseable trade date, non-negative volume, ascending order)
- [x] 5.4 Persistence assertion trimmed: the upsert-to-DB step was not duplicated here because the persistence path is already covered by `tests/integration_data.py` with `ControlledMarketDataProvider`. The gated test focuses on the jqdatasdk real-output contract (the only thing fakes cannot verify). Minimal adjustment per scope discipline.
- [x] 5.5 Open Question recorded in `design.md`: jqdatasdk real output shape to be verified by a maintainer with credentials (gated test currently skipped — no credentials in dev env)

## 6. Verification

- [x] 6.1 Run `ruff check` and `ruff format --check` across new and modified files — passed
- [x] 6.2 Run `mypy` on `packages/core/src` with no errors — passed
- [x] 6.3 Run the full default test suite — 475 passed, 1 skipped (gated JoinQuant test, no credentials)
- [x] 6.4 Run the JoinQuant unit tests (no credentials) — 16 passed
- [x] 6.5 Run `openspec validate --all` — 35 passed, 0 failed
- [x] 6.6 Decision recorded in `design.md`: CI does NOT install the `joinquant` extra and does NOT run the gated test (no JoinQuant secrets in CI); the gated test is local/manual for maintainers with credentials
