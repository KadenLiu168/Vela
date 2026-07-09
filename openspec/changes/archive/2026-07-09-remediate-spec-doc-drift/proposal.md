## Why

OpenSpec consistency audit (2026-07-09) found 11 low-risk findings where the fix target is already unambiguous and the change is text/config/small-code only — no architecture decision, no behavior redesign. These are the "directly fixable" batch: stale spec text, sibling-spec contradictions, doc gaps, and three small implementation-drift fixes that align code to an already-correct spec. Shipping them now clears the cheap, high-confidence debt so the higher-risk items (API config caching C1, missing API contract specs A1/A2, front-end label/heading drift C2/C3) can be discussed separately.

## What Changes

Spec text corrections (align stale/incorrect spec wording to verified reality):
- `command-palette` spec: replace removed route `/signals/demo-signal` with `/signals` (matches `web-frontend-app` and `App.tsx` nav).
- `card-type-scale` spec: drop `IBM Plex Mono` font description and align the `--font-display` token + `@font-face`/preload requirement to `Inter Variable` per the authoritative `design-system` spec (which already mandates Inter Variable and forbids IBM Plex Mono).
- `dashboard-aggregation` spec: change "strategy name" to "strategy id" (matches `database-migrations` rename and `backtest` model).
- `market-data` + `market-price-panel-loading` specs: add cross-reference between their overlapping `Multi-ETF market price panel loading` requirement to reduce reviewer confusion.

Documentation gaps:
- `apps/web/README.md`: add missing `styles/` and `utils/` to the Structure section.
- `docs/browser-manual-acceptance.md` (and any doc still referencing it): remove stale `/signals/demo-signal` references.
- `docs/architecture.md`: populate with the component → OpenSpec spec → implementation map (currently a 0-byte file).

Small code fixes that align implementation to an already-correct spec (no requirement change):
- CLI `sync-etf-pool` (`apps/cli/src/vela_cli/main.py`) — **WITHDRAWN (false positive, verified during apply)**: `ETFPoolSyncResult` (`packages/core/src/vela_core/etf_pool_sync.py:11`) has no `status` field, and failures are caught upstream by the CLI `try/except` wrapper (`main.py:234`) which `return 1`s **before** reaching `_print_etf_pool_sync_summary` (`main.py:469`). On the only reachable path the summary prints, the sync succeeded — the hard-coded `"success"` is correct. No code change.
- Frontend Dashboard rebalance frequency: capitalize the displayed value (`weekly`→`Weekly`, `monthly`→`Monthly`) to satisfy `web-rebalance-frequency-display` (`apps/web/src/pages/DashboardPage.tsx:343`). No spec change — spec already mandates "Weekly"/"Monthly".
- `apps/web` stylelint config: add an explicit rule forbidding `:root` blocks outside `tokens.css` (currently only enforced by convention/override).

## Capabilities

### New Capabilities

_(none — this change remediates existing specs/docs, it introduces no new capability.)_

### Modified Capabilities

Specs whose content is corrected (all MODIFIED deltas, no requirement semantics change unless noted):
- `command-palette`: navItem route corrected from `/signals/demo-signal` to `/signals`.
- `card-type-scale`: font description corrected to `Inter Variable`; `@font-face`/preload requirement aligned to the authoritative `design-system` spec (no IBM Plex Mono).
- `dashboard-aggregation`: "strategy name" → "strategy id".
- `market-data`: add cross-reference to `market-price-panel-loading` for the shared `Multi-ETF market price panel loading` requirement.
- `market-price-panel-loading`: add cross-reference to `market-data` for the shared `Multi-ETF market price panel loading` requirement.

> Note: `design-system` was initially considered for a stale `@import` path description (B5), but verification showed `tokens.css` is correctly located at `apps/web/src/styles/tokens.css` and the design-system font requirement already mandates `Inter Variable`. The `@import` line itself is absent from `styles.css` today, which is a separate drift investigation (not in this batch). `design-system` is therefore NOT modified here.

> Note: code fixes (CLI summary, frontend frequency capitalization, stylelint rule) do NOT change any spec requirement — they bring implementation into compliance with specs that are already correct, so they are implementation tasks, not capability deltas.

## Impact

- Affected specs: `openspec/specs/{command-palette,card-type-scale,design-system,dashboard-aggregation,market-data,market-price-panel-loading}/spec.md`
- Affected docs: `apps/web/README.md`, `docs/browser-manual-acceptance.md`, `docs/architecture.md`
- Affected code/config: `apps/cli/src/vela_cli/main.py`, `apps/web/src/pages/DashboardPage.tsx`, `apps/web` stylelint config
- Dependencies: none new. No API contract, no DB migration, no runtime behavior change beyond the two cosmetic code fixes (CLI summary wording, dashboard label casing).
- Risk: Low. All changes are either spec/doc text or localized, verified-correct code edits. The three code edits are covered by existing tests (`apps/cli` tests, `apps/web` `App.test.tsx` / `DashboardPage` tests, stylelint run in CI).
- Out of scope (explicitly deferred, needs discussion): D1 (20 spec Purpose placeholders — intent confirmation required), C1 (API config caching rewrite), A1/A2 (new API contract specs), C2/C3 (front-end PanelHeading labels & dashboard heading responsive ladder).
