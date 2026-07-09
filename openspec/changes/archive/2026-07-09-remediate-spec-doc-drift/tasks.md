# Tasks — remediate-spec-doc-drift

## 1. Spec text corrections (MODIFIED deltas)

- [x] 1.1 `command-palette/spec.md` — change `**page** rows: ... (/, /signals/demo-signal, /backtests)` to `/signals` (line 43).
  - **Verify**: `grep -rn "demo-signal" openspec/specs/command-palette/spec.md` returns nothing.
- [x] 1.2 `card-type-scale/spec.md` — replace `IBM Plex Mono` wording in the `Display font family is exposed for card titles` requirement (lines 73-122) with `Inter Variable`; align `@font-face`/preload requirement to the `design-system` decision.
  - **Verify**: requirement body now uses `Inter Variable`; the only remaining `IBM Plex Mono` mentions are in the forbidding/supersession note (lines 86-88) — intentional, not leftover drift.
- [x] 1.3 `dashboard-aggregation/spec.md` — change "strategy name" → "strategy id" in the `Dashboard recent backtest summary` scenario (line 57).
  - **Verify**: `grep -n "strategy name" openspec/specs/dashboard-aggregation/spec.md` returns nothing.
- [x] 1.4 `market-data/spec.md` + `market-price-panel-loading/spec.md` — append the cross-reference blockquote to the `Multi-ETF market price panel loading` requirement in both.
  - **Verify**: both files contain the cross-reference note; scenarios unchanged.

## 2. Documentation gaps

- [x] 2.1 `apps/web/README.md` — add `styles/` and `utils/` to the Structure section.
  - **Verify**: Structure section lists `styles/` and `utils/`.
- [x] 2.2 `docs/browser-manual-acceptance.md` (and any doc still referencing it) — remove `/signals/demo-signal` references; replace with `/signals` where a route is meant.
  - **Verify**: `grep -rn "demo-signal" docs/` returns nothing (outside archived `openspec/changes/` history).
- [x] 2.3 `docs/architecture.md` — populate with the component → OpenSpec spec → implementation map (derived from the audit's architecture overview).
  - **Verify**: file is non-empty and lists the backend/API/CLI/web/data/config/test/doc components with their spec and implementation paths.

## 3. Small code fixes (align to already-correct spec)

- [x] 3.1 CLI `sync-etf-pool` — **WITHDRAWN (false positive)**. Audit claimed `result.status` exists on `ETFPoolSyncResult`, but the dataclass (`packages/core/src/vela_core/etf_pool_sync.py:11`) has no `status`/`failed_symbols`/`error_message` fields. Failures are caught upstream by the CLI `try/except` wrapper (`apps/cli/src/vela_cli/main.py:234`) which `return 1` **before** reaching `_print_etf_pool_sync_summary` (`:469`). On the only reachable path the summary prints, the sync succeeded — the hard-coded `"success"` is correct. No code change; the invariant stays enforced by the existing exception path.
- [x] 3.2 Frontend Dashboard rebalance frequency (`apps/web/src/pages/DashboardPage.tsx:343`) — capitalize the displayed `frequency` value (`weekly`→`Weekly`, `monthly`→`Monthly`).
  - **Verify**: `npm --prefix apps/web test` passes; existing tests assert the `rebalance` **label** (`getByText("rebalance")`) but NONE assert the capitalized **value** — fixtures use `frequency: "weekly"` (`App.test.tsx:1747`). A regression test for the casing could be added separately; this change does not introduce one (minimal scope).
- [x] 3.3 `apps/web` stylelint invariant — `stylelint-config-standard` has **no** built-in rule for "no `:root` outside `tokens.css`", so the explicit rule is implemented as a zero-dependency guard script `scripts/check-css-root.mjs` (mirrors the repo's existing `scripts/build-tokens-reference.mjs` convention; strips `/* */` comments then fails if any non-`tokens.css` file declares a `:root {` block). Exposed as a standalone `apps/web/package.json` script `lint:css:root`.
  - **Verify**: `npm --prefix apps/web run lint:css:root` passes today (only `tokens.css` has a real `:root` block; `styles.css` references `:root` only inside a comment, which the guard strips). A real `:root {` block in another css file fails the script (verified by probe).
  - **NOTE (R7, out of scope)**: the upstream `stylelint` step in `lint:css` (unchanged by this change) currently FAILS on two **pre-existing** errors in `apps/web/src/styles.css` — `line-height: 1` (line 520) and `border-radius: 1px` (line 528) — both disallowed by `declaration-property-value-disallowed-list` and both violate the `design-system` capability (line-height MUST use a `--leading-*` token; radius MUST use a `--radius-*` token). These predate this change (this change does not touch `styles.css`), so they are NOT fixed here and the guard is deliberately NOT chained into the already-failing `lint:css` (it would be unreachable). They need a separate `design-system` compliance change.

## 4. Validation & archive

- [x] 4.1 Run `openspec validate remediate-spec-doc-drift` — all artifacts valid.
- [x] 4.2 Run relevant test suites: `pytest` (CLI/core), `npm --prefix apps/web test` and `lint:css` (lint:css fails on pre-existing R7 errors — out of scope, documented at 3.3).
- [x] 4.3 Archive the change (`openspec archive remediate-spec-doc-drift`) so the 5 MODIFIED deltas merge into `openspec/specs/`.
  - **Verify**: `grep -rn "IBM Plex Mono" openspec/specs/card-type-scale/spec.md` returns nothing and `grep -rn "demo-signal" openspec/specs/command-palette/spec.md` returns nothing after archive.

## Notes

- Out of scope (separate proposals): D1 (20 spec Purpose placeholders), C1 (API config caching), A1/A2 (new API contract / error specs), C2/C3 (front-end PanelHeading labels & dashboard heading responsive ladder), and the `design-system` `@import` investigation (B5).
