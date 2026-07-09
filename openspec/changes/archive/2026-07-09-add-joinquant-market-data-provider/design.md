## Context

`BaseMarketDataProvider` (in `packages/core/src/vela_core/base_market_data_provider.py`) orchestrates fetch → normalize → validate → retry, and exposes a hook set that subclasses fill: `name`, `_source_label`, `_column_map`, `_fetch_rows` (with `@retry`), `_format_request_symbol`, and optionally `_sort_prices`. The constructor accepts an injectable `source` module, defaulting to `import_module("akshare")`.

Two subclasses exist today: `AkShareMarketDataProvider` (calls `akshare.fund_etf_hist_em`) and `TencentMarketDataProvider` (calls `akshare.stock_zh_a_hist_tx`, default). Both depend on the `akshare` package, so the `MarketDataProvider` abstraction has never been exercised against a non-akshare library despite the spec's "Provider implementation independence" requirement. The base `_normalize_rows` checks `set(self._column_map.values()) - set(rows.columns)` and iterates via `rows.iterrows()`, so it assumes a pandas DataFrame with named columns.

Credentials and config today: `AppConfig` is a frozen pydantic `BaseModel` loaded from git-tracked YAML (`config/strategy_v1.yaml`, `config/etf_pool.yaml`). There is no environment-variable loading anywhere in `packages/core/src` (verified: zero matches for `os.environ|BaseSettings|pydantic_settings|getenv`), even though `pydantic-settings` and `python-dotenv` are declared dependencies. `.gitignore` already ignores `.env` and `.env.*`, but no `.env` file exists.

## Goals / Non-Goals

**Goals:**
- Add a `JoinQuantMarketDataProvider` that satisfies the existing `MarketDataProvider` contract using `jqdatasdk`, proving the abstraction against an independent library.
- Handle JoinQuant's three real differences (date in index, `XSHG`/`XSHE` symbol suffix, mandatory `auth`) entirely within the subclass.
- Establish a credential-loading path that never touches git-tracked files and never hardcodes secrets.
- Keep the default provider (Tencent), the CLI/API default instantiation paths, and the base class unchanged.

**Non-Goals:**
- No `build_provider(name)` factory, no CLI/API default-path refactor (deferred to Phase 3 multi-source comparison).
- No formal `JoinQuantSettings` via `pydantic-settings.BaseSettings` (a `.env` + `os.environ` transition is sufficient for this step; a formal settings module can follow).
- No multi-source comparison harness, no ExecutionProvider, no real-time trading.
- No change to `AppConfig`, the calculation layer, or the persistence layer.

## Decisions

### D1: Thin subclass, no base-class changes
Fill the existing hooks; do not extend `BaseMarketDataProvider` with new hook points.
- **Alternative considered**: add a `_reshape_rows` hook to the base so subclasses can normalize DataFrame shape before `_normalize_rows` runs. Rejected — `_fetch_rows` is already the designated place for source-specific transformation, and `reset_index()` fits there. Adding a base hook for one subclass is premature.

### D2: Credentials via `.env` + `os.environ`, not `AppConfig`
`__init__` calls `dotenv.load_dotenv()` then reads `JQ_USERNAME` / `JQ_PASSWORD` from `os.environ`. Missing credentials raise a clear `MarketDataProviderError`.
- **Alternative A**: store credentials in `config/*.yaml` and load via `AppConfig`. Rejected — `config/*.yaml` is git-tracked (`git ls-files config/` confirms `strategy_v1.yaml`, `etf_pool.yaml`), so secrets would be committed. `AppConfig` also has no credential field and is frozen YAML-only.
- **Alternative B**: introduce a formal `JoinQuantSettings(BaseSettings)` from `pydantic-settings`. Deferred — heavier than this step needs; `.env` + `os.environ` is the minimal 12-factor path and `.gitignore` already covers it.

### D3: Lazy `auth`, exactly once per process, via module-level flag
`__init__` authenticates only if a module-level `_JQ_AUTH_DONE` flag is unset, then sets it. `jqdatasdk.auth` is process-global state, so per-instance auth would cause redundant authentications under multiple instantiations (e.g. API per-request).
- **Alternative**: authenticate on every `_fetch_rows`. Rejected — redundant and risks quota/counting anomalies.

### D4: `reset_index()` with explicit `index.name`
In `_fetch_rows`, set `df.index.name = "trade_date"` before `df = df.reset_index()`, so the resulting column is named `trade_date` and matches `_column_map["trade_date"]`.
- **Alternative**: rely on jqdatasdk's default index name. Rejected — if the default `index.name` is `None`, `reset_index()` produces a column literally named `"index"`, which fails the base `_normalize_rows` missing-column check. Pinning the name removes the dependency on jqdatasdk's default.

### D5: No factory, no CLI/API change
`JoinQuantMarketDataProvider` is instantiated only in the gated integration test and explicit opt-in paths. CLI (`main.py:322,329`) and API (`main.py:60`) keep `TencentMarketDataProvider()`.
- **Alternative**: introduce `build_provider(name)` defaulting to `"tencent"` and route CLI/API through it. Rejected — only two call sites exist, the spec locks the default to Tencent with explicit scenarios, and the factory has no second consumer until Phase 3. Touching the default path adds regression surface for zero benefit this step.

### D6: `jqdatasdk` as PEP 621 optional dependency
Add `[project.optional-dependencies]` `joinquant = ["jqdatasdk"]`. The package is imported lazily via `import_module("jqdatasdk")` inside `__init__`, never at module top level, so `import vela_core` succeeds without the extra installed.
- **Alternative**: add to `[dependency-groups]` (PEP 735). Rejected — dependency-groups are dev-only groups; an optional runtime backend that contributors opt into is the extras use case. This is the project's first extras entry alongside the existing dependency-groups; CI must decide on a matrix (see Open Questions).

### D7: Gated integration smoke test
A `@pytest.mark.skipif(not env)` test fetches a real `510300.XSHG` daily bar and writes it through `upsert_market_prices`, verifying jqdatasdk's real output contract (date format, index name, auth flow) that fakes cannot cover.
- **Alternative**: mandatory integration test (blocks CI without credentials) or no integration test. Both rejected — mandatory excludes credential-less contributors; none leaves R1 (real contract) permanently unverified.

## Risks / Trade-offs

- **[R1 jqdatasdk real contract unverified by fakes]** → Mitigation: gated smoke test (D7); pin `index.name` explicitly (D4) so the one known fragility is removed regardless of jqdatasdk defaults.
- **[Import-time breakage if jqdatasdk imported at module top]** → Mitigation: lazy `import_module` inside `__init__`/`_fetch_rows` only; extend the contract-independence test to assert `market_data_provider.py` has no `jqdatasdk`/`joinquant`; add a test that `import vela_core` succeeds without the extra.
- **[Credential leakage via git-tracked config]** → Mitigation: `.env` (gitignored) only; `.env.example` committed with key names and no values; no credentials in `config/*.yaml` or `AppConfig`. Note: `.gitignore`'s `.env.*` pattern initially swallowed `.env.example`; a `!.env.example` negation was added so the template is committable while real `.env` stays ignored.
- **[Redundant auth / quota anomalies]** → Mitigation: module-level single-auth flag (D3).
- **[Dual dependency-declaration mechanisms]** → The project gains PEP 621 extras alongside PEP 735 groups. Trade-off accepted; `uv.lock` correctly records `jqdatasdk` under `[package.optional-dependencies] joinquant` with marker `extra == 'joinquant'`, so `uv sync` without the extra does not install it.
- **[Abstraction claim overreach]** → This step validates library-independence (non-akshare), not data-shape independence (the base remains pandas-coupled via `iterrows`/`columns`). Spec wording is scoped accordingly to avoid overclaiming.

## Open Questions

- **jqdatasdk exact output**: date string format, column names, index name. Resolved at runtime by the gated smoke test; the fake-module unit tests use a representative shape and are adjusted if the smoke test reveals a mismatch. (As of this change the gated test is skipped — no credentials in the dev environment — so the real contract remains to be verified by a maintainer with a JoinQuant account.)
- **CI matrix (resolved)**: CI does NOT install the `joinquant` extra and does NOT run the gated test (no JoinQuant secrets in CI). The gated `test_joinquant_integration.py` is local/manual: a maintainer with credentials runs it before relying on JoinQuant data. The fake-module unit tests run in CI and cover the provider logic; the smoke test covers only the jqdatasdk real-output contract that fakes cannot.
