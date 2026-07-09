## Context

The OpenSpec consistency audit (2026-07-09) produced 20 findings across four categories. Eleven of them are low-risk and have an unambiguous fix target: stale/incorrect spec text, sibling-spec contradictions, doc gaps, and three small implementation-drift fixes that align code to an already-correct spec. This change remediates exactly that batch. The audit's higher-risk items (API config caching C1, missing API contract specs A1/A2, front-end PanelHeading labels & dashboard heading responsive ladder C2/C3, and the 20 spec Purpose placeholders D1) are explicitly deferred to separate proposals that require design decisions or intent confirmation.

Verified evidence behind each fix:
- `command-palette` spec line 43 references `/signals/demo-signal`; `web-frontend-app` spec forbids it and `App.tsx` nav uses `/signals`.
- `card-type-scale` spec mandates `IBM Plex Mono`; authoritative `design-system` spec mandates `Inter Variable` and forbids IBM Plex Mono `@font-face`.
- `dashboard-aggregation` spec line 57 says "strategy name"; `database-migrations` renamed it to `strategy_id` and the `backtest` model / `dashboard_aggregation.py` use `strategy_id`.
- `market-data` and `market-price-panel-loading` both define `Multi-ETF market price panel loading` with no cross-link, causing reviewer confusion.
- `apps/web/README.md` Structure section omits `styles/` and `utils/`.
- `docs/browser-manual-acceptance.md` and some archived changes still reference `/signals/demo-signal`.
- `docs/architecture.md` is a 0-byte file.
- CLI `sync-etf-pool` hard-codes `"ETF pool sync status: success"` — **WITHDRAWN (false positive, verified during apply)**: `ETFPoolSyncResult` (`packages/core/src/vela_core/etf_pool_sync.py:11`) has no `status` field, and failures are caught upstream by the CLI `try/except` wrapper (`main.py:234`) which `return 1`s **before** reaching `_print_etf_pool_sync_summary` (`main.py:469`). On the only reachable path the summary prints, the sync succeeded — the hard-coded `"success"` is correct. No code change.
- Frontend Dashboard renders `strategy.rebalance.frequency` raw (`"weekly"/"monthly"`) at `apps/web/src/pages/DashboardPage.tsx:343`, but `web-rebalance-frequency-display` requires `"Weekly"/"Monthly"`.
- `apps/web` stylelint config enforces the "no `:root` outside tokens.css" invariant only by convention/override, with no explicit forbidding rule.

## Goals / Non-Goals

**Goals:**
- Correct the 6 spec files so they match verified implementation reality.
- Close the documentation gaps (`apps/web/README.md`, `docs/browser-manual-acceptance.md`, `docs/architecture.md`).
- Fix the 3 small code drifts (CLI summary, dashboard frequency casing, stylelint rule) to comply with already-correct specs.

**Non-Goals:**
- No new API contract specs (A1/A2) — separate proposal.
- No API config-caching rewrite (C1) — separate proposal, has hot-reload trade-off.
- No front-end PanelHeading label / dashboard heading responsive-ladder changes (C2/C3) — separate proposal, involves UX wording decisions.
- No spec Purpose authoring (D1) — requires business-intent confirmation, separate proposal.
- No new capabilities, no DB migrations, no runtime behavior beyond the (two) cosmetic code fixes — the CLI `sync-etf-pool` "success" wording was verified a false positive (no `status` field; failures handled upstream) and is NOT changed.

## Decisions

**D1 — Keep spec deltas as MODIFIED, not REMOVED.** The stale requirements still describe a real capability; only wording/route is wrong. Full requirement blocks are reproduced in the deltas so nothing is lost at archive time.

**D2 — Drop `design-system` from the batch (B5).** Verification showed `tokens.css` is correctly at `apps/web/src/styles/tokens.css`, and the design-system font requirement already mandates `Inter Variable`. The `@import "./tokens.css"` line is actually *absent* from `styles.css` today — a real but separate drift (spec requires the import; implementation may load tokens another way). That needs its own investigation, so it is excluded from this low-risk batch to avoid shipping an incorrect delta.

**D3 — Fix code to match spec, not vice versa, for C5/C6.** For `web-rebalance-frequency-display` (C5) and CLI summary (C6), the spec is already correct and the code is the drift. Fix the code. No spec delta needed for those.

**D4 — Cross-reference as a non-normative note, not a requirement change.** The `market-data` / `market-price-panel-loading` overlap (D5) is documentation clarity, not a behavior change; appended as a blockquote note inside the existing requirement, preserving all scenarios.

**D5 — stylelint rule scope limited to `apps/web`.** The "no `:root` outside tokens.css" invariant already exists for the web frontend; we add an explicit rule there only. No change to `packages/core` or `apps/api` lint configs.

## Risks / Trade-offs

- [Risk] Editing archived-style spec text could conflict if another in-flight change also touches these specs. → Mitigation: these 6 specs are not in any other active change root; verify with `openspec list` before archiving.
- [Risk] Capitalizing rebalance frequency (C5) changes a visible label from "weekly" to "Weekly". → Mitigation: matches the spec contract; covered by `App.test.tsx` / `DashboardPage` tests which assert the "Weekly"/"Monthly" value — those tests currently expect the capitalized form and will now pass.
- [Risk] Removing the hard-coded "success" string (C6) surfaces a non-"success" status if the sync ever fails. → Mitigation: this is the *correct* behavior; existing CLI tests cover the summary output shape.
- [Trade-off] The `docs/architecture.md` content is hand-derived from the audit's component map; it is advisory and may drift again. → Mitigation: keep it short and note it is generated from the audit, not a living doc.

## Migration Plan

1. Apply spec deltas: `openspec archive` will merge the 6 MODIFIED deltas into `openspec/specs/`.
2. Doc edits (`apps/web/README.md`, `docs/browser-manual-acceptance.md`, `docs/architecture.md`) are plain file edits.
3. Code edits (CLI summary, DashboardPage frequency, stylelint config) are localized and covered by existing test suites.
4. Rollback: all changes are text/config; `git revert` of the commit restores prior state. No migration step or data change.

## Open Questions

- Should the `design-system` `@import` absence in `styles.css` be treated as a spec violation (fix code to add the import) or a spec over-constraint (relax the requirement)? Deferred — not part of this change.
- D1 (20 spec Purpose placeholders) needs business-intent confirmation before authoring; deferred to its own proposal.
