## Context

`AkShareMarketDataProvider` (`packages/core/src/vela_core/akshare_market_data_provider.py`, ~421 lines) and `TencentMarketDataProvider` (`tencent_market_data_provider.py`, ~386 lines) implement the `MarketDataProvider` Protocol defined in `market_data_provider.py`. They share roughly 300 lines of near-verbatim code: the `get_etf_daily_prices` fetch/normalize orchestration, the `_normalize_rows` skeleton, and the entire row-parsing/validation helper set (`_parse_decimal`, `_parse_price`, `_parse_volume`, `_parse_trade_date`, `_validate_ohlc`, `_require_value`, `_is_missing`, `_format_date`, `_validation_error`, `_error_message`). The 2026-07-08 code quality review flagged this as [M1] high-priority.

The duplication also masks three divergences that emerged only on close reading:

1. **Ordering**: AkShare returns `sorted(prices, key=lambda p: p.trade_date)`; Tencent returns `prices` in source order. The spec defines no ordering requirement for either provider.
2. **Error-type ownership**: `MarketDataProviderError` is defined in the AkShare module and reverse-imported by Tencent (`from vela_core.akshare_market_data_provider import MarketDataProviderError`), contradicting the spec's "Provider implementation independence" requirement.
3. **Wording**: AkShare emits `"invalid date"`; Tencent emits `"invalid trade date"` for the same failure.

Their genuine differences reduce to: column names (Chinese vs English), volume presence (AkShare requires `成交量`; Tencent has none and drops `amount`), source call (`fund_etf_hist_em` vs `stock_zh_a_hist_tx`), symbol transformation (Tencent prefixes `sh`/`sz`), and the sort behavior above.

## Goals / Non-Goals

**Goals:**
- Eliminate the ~300 lines of duplicated parsing/validation/orchestration logic via a single shared base.
- Make the genuine per-provider differences explicit and localized to a small hook set.
- Close the three latent divergences (ordering, error-type ownership, wording) with deliberate decisions.
- Preserve all existing externally observable behavior except the explicitly-decided Tencent ordering change.
- Keep `MarketDataProviderError`, `AkShareMarketDataProvider`, `TencentMarketDataProvider`, `DailyPrice`, and `MarketDataProvider` exported from `vela_core` under their existing names.

**Non-Goals:**
- Vectorizing the pandas `iterrows` row loop (separate concern, tracked as [P4] in the quality review).
- Concurrent ETF fetching (separate concern, [P3]).
- Consolidating the duplicated AkShare/Tencent validation *requirements* in the spec into a single provider-agnostic block (possible follow-up; this change only adds the ordering + error-type requirements).
- Changing retry policy, the `DailyPrice` value object, or the `MarketDataProvider` Protocol signature.
- Touching the `apps/api` or `apps/cli` layers (call sites verified to need no change).

## Decisions

### Decision 1: Template-method base class (Option A)

Introduce `BaseMarketDataProvider` in a new module `base_market_data_provider.py` (or within `market_data_provider.py`; see Decision 3 for placement of the error type). The base holds the orchestration and parsing as `final` methods and exposes a small hook set subclasses override:

| Hook | Type | AkShare | Tencent |
|---|---|---|---|
| `name` | class attr | `"akshare"` | `"tencent"` |
| `_source_label` | class attr | `"akshare"` | `"tencent"` |
| `_column_map` | class attr, `Mapping[str, str]` | `trade_date→日期, open→开盘, high→最高, low→最低, close→收盘, volume→成交量` | `trade_date→date, open→open, high→high, low→low, close→close` (no volume) |
| `_fetch_rows` | abstract, `@retry` | `source.fund_etf_hist_em(period="daily", adjust="")` | `source.stock_zh_a_hist_tx(adjust="")` |
| `_format_request_symbol` | hook, default passthrough | passthrough | `sh`/`sz` prefix |
| `_sort_prices` | hook, default ascending sort | default | default (behavior change) |

The base `_normalize_rows` derives required columns as `set(_column_map.values())` and `_extract_row` parses each mapped field; volume is parsed only when `"volume"` in `_column_map`, otherwise `volume=None`. The `amount` column (Tencent) is ignored automatically because it is absent from the map.

**Alternatives considered:**
- **Option B — shared parser module of free functions**: kills parsing duplication but leaves the ~30-line `get_etf_daily_prices` orchestration duplicated in each provider. Rejected: the orchestration is the most error-prone part (try/fetch → try/normalize error wrapping) and duplicating it defeats much of the purpose.
- **Option C — hybrid (base for orchestration + separate parser module)**: marginally more modular but splits closely-coupled logic across two files for no behavioral benefit. Rejected as over-engineering for two providers.

### Decision 2: Unify result ordering to ascending by `trade_date`

Both providers return `DailyPrice` sequences sorted ascending by `trade_date`. The base `_sort_prices` default implements this; neither subclass overrides it.

**Rationale**: The spec previously defined no ordering, leaving Tencent's output order undefined (it relied on `stock_zh_a_hist_tx`'s unspecified return order). AkShare already sorted, evidencing that source order is not reliable. Downstream `market_data_fetcher` (`market_data_fetcher.py:137,143`) extends a list then batch-upserts via `upsert_market_prices` by primary key `(etf_id, trade_date)` — verified order-independent — so changing Tencent to sort is safe.

**Alternative considered**: preserve the divergence via the `_sort_prices` hook (Tencent passthrough). Rejected because it codifies an undeclared source-order assumption as a feature; a future provider returning unordered data would silently propagate. Unifying closes the spec gap and makes the contract explicit.

### Decision 3: Relocate `MarketDataProviderError` to the contract module

`MarketDataProviderError` moves from `akshare_market_data_provider.py` into `market_data_provider.py`, alongside `DailyPrice` and the `MarketDataProvider` Protocol. `packages/core/src/vela_core/__init__.py` is updated to import it from the new location; the public name `vela_core.MarketDataProviderError` is unchanged.

**Rationale**: The error type is part of the provider contract, not an AkShare implementation detail. Tencent reverse-importing it from the AkShare module violates the spec's "Provider implementation independence" requirement. The existing test `test_provider_contract_module_remains_source_library_independent` asserts the contract module source contains neither `"akshare"` nor `"pandas"`; the error class name contains neither token, so the assertion remains green.

The `BaseMarketDataProvider` class lives in a new `base_market_data_provider.py`. Confirmed during implementation: the base module does not `import pandas` directly — it accepts the rows object as `Any` and calls `.iterrows()`/`.columns` duck-typed. The contract-module independence test (scoped to `market_data_provider.py`) is therefore unaffected regardless.

### Decision 4: Rename constructor parameter `akshare_module` → `source`

Both providers' `__init__` change from `(self, akshare_module=None)` / `self._akshare` to `(self, source=None)` / `self._source`. Tencent's parameter was misleadingly named after a different provider.

**Rationale**: The parameter accepts the underlying AkShare library module (used by both providers, since Tencent delegates to `stock_zh_a_hist_tx` on the same library). `source` is accurate and provider-agnostic.

**Compatibility**: Verified call sites — `apps/api/src/vela_api/main.py:60` and `apps/cli/src/vela_cli/main.py:322,329` all construct with no arguments (`TencentMarketDataProvider()`). No call site uses the `akshare_module=` keyword. The rename is therefore non-breaking in practice. Tests construct positionally or with no args.

### Decision 5: Unify validation wording and error-detail labels

The shared `_parse_trade_date` emits `"invalid trade date"` on parse failure (matching Tencent's existing wording and the helper's own name). AkShare's previous `"invalid date"` is retired.

In addition, the provider label inside error-detail strings is unified to lowercase: the fetch/normalization/missing-columns/row-validation detail segments now use `self._source_label` (e.g. `"akshare fetch failed"`, `"tencent row validation failed ..."`) instead of the previously inconsistent capitalized forms (`"AkShare"` camelCase vs `"Tencent"` PascalCase). The error-message prefix was already lowercase (`"akshare market data provider error ..."`), so this makes the detail segment consistent with the prefix and removes the cross-provider capitalization inconsistency.

**Rationale**: `"trade date"` is more precise and consistent with the `_parse_trade_date` function name and the `DailyPrice.trade_date` field. The lowercase detail label is consistent with the already-lowercase prefix. No test asserts the capitalized detail form (verified by grep — all `"AkShare"`/`"Tencent"` occurrences in tests are class names or the lowercase `name` attribute string), so the change is non-breaking for the test suite. AkShare tests do not pin the `"invalid date"` reason string either (they assert source/symbol/date-range/row/column/reason-presence context, not the reason text), so no test wording update was required. All other validation reason strings (`"invalid decimal"`, `"decimal must be finite"`, `"price must be greater than zero"`, `"volume must be an integer"`, `"volume must be non-negative"`, `"required value is missing"`, `"high must be at least..."`, `"low must be at most..."`) are already identical between the two providers and remain unchanged.

## Risks / Trade-offs

- **Tencent ordering behavior change** → Mitigated: downstream upsert is PK-based and order-independent (verified). The change is explicit in the spec delta and surfaced in the proposal's Impact section. If any undiscovered consumer relied on Tencent's previous source order, it would surface as a test failure during implementation.
- **Inheritance depth / future provider with very different row shape** → Mitigated: the hook set (`_column_map`, `_fetch_rows`, `_format_request_symbol`, `_sort_prices`) is small and composable; a provider that cannot fit the column-map model can override `_extract_row` or `_normalize_rows` directly without touching the shared parsing helpers.
- **`_sort_prices` hook may invite future divergence** → Trade-off accepted: keeping it as an overridable hook (rather than hardcoding sort in `_normalize_rows`) preserves extensibility, but the default is ascending and both subclasses use it. Documented in design to discourage overriding without justification.
- **`MarketDataProviderError` relocation touches the contract module** → Mitigated: the contract-module independence test is scoped to `"akshare"`/`"pandas"` token absence, which holds. Re-export path updated in `__init__.py`.
- **Base class module placement** → Minor open question: whether `BaseMarketDataProvider` lives in `market_data_provider.py` (contract module) or a new `base_market_data_provider.py`. Resolved at implementation time by checking whether the base module needs to `import pandas`; if it does, a separate module keeps the contract module clean. Either way the public API is unaffected.
