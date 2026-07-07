## 1. Register card-type-scale tokens in tokens.css

- [ ] 1.1 Add `--card-meta-size: 11px;` and `--leading-meta: 1.4;` to the typography section of `apps/web/src/styles/tokens.css`
- [ ] 1.2 Add `--card-body-size: 14px;` and `--leading-body-card: 1.5;` to the same section
- [ ] 1.3 Add `--card-emphasis-size: 28px;` and `--leading-emphasis: 1.3;` to the same section
- [ ] 1.4 Add `--card-display-size: 40px;` and `--leading-display-card: 1.15;` to the same section
- [ ] 1.5 Add `--tracking-meta: 0.06em;` and `--tracking-numeral: -0.01em;` to the same section
- [ ] 1.6 Add `--font-display: "Departure Mono", "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;` to the typography-families section
- [ ] 1.7 Update the leading comment block in `tokens.css` to list "Card typography ladder (meta / body / emphasis / display)" under the Typography groups

## 2. Load display font asset

- [ ] 2.1 Download `DepartureMono-Regular.woff2` (and `DepartureMono-Medium.woff2` if used) into `apps/web/public/fonts/`; verify license is OFL / SIL / MIT / Apache-2.0 before committing
- [ ] 2.2 Add `@font-face` rules for `"Departure Mono"` in `apps/web/src/styles.css` (one per weight) with `font-display: swap` and `src` referencing the woff2 files
- [ ] 2.3 Add `<link rel="preload" as="font" type="font/woff2" crossorigin href="/fonts/DepartureMono-Regular.woff2">` to `apps/web/index.html` (placed after the existing InterVariable preload)

## 3. Re-wire card role rules in styles.css

- [ ] 3.1 Rewrite `.compact-list dt` to use `var(--card-meta-size)`, `var(--leading-meta)`, `var(--font-weight-semibold)`, `text-transform: uppercase`, `letter-spacing: var(--tracking-meta)`
- [ ] 3.2 Rewrite `.compact-list dd` to use `var(--card-body-size)`, `var(--leading-body-card)`, `var(--font-weight-medium)`
- [ ] 3.3 Rewrite `.metric span` to use `var(--card-meta-size)`, `var(--leading-meta)`, `var(--font-weight-semibold)`, uppercase + tracking
- [ ] 3.4 Rewrite `.metric strong` to use `var(--card-emphasis-size)`, `var(--leading-emphasis)`, add `font-variant-numeric: tabular-nums` and `letter-spacing: var(--tracking-numeral)`
- [ ] 3.5 Rewrite `.panel-heading h3` to keep size at `var(--text-subheading)` but add `font-family: var(--font-display)` and adjust tracking to `var(--tracking-subheading)`
- [ ] 3.6 Rewrite `.panel-heading span` (eyebrow) to use `var(--card-meta-size)`, `var(--leading-meta)`, `var(--font-weight-regular)` (NOT semibold) to differentiate from pill, uppercase + tracking
- [ ] 3.7 Rewrite `.panel-primary` (and the `.dashboard-page .panel-primary` override, which will be deleted in step 4) to use `var(--card-emphasis-size)`, `var(--leading-emphasis)`, tabular-nums, `var(--tracking-numeral)`
- [ ] 3.8 Rewrite `.status-pill` to use `var(--card-meta-size)`, `var(--leading-meta)`, `var(--font-weight-medium)`, uppercase + tracking
- [ ] 3.9 Rewrite `.dashboard-button` to use `var(--card-body-size)`, `var(--leading-body-card)`; preserve the existing padding; verify the per-view primary CTA (lime fill) remains intact
- [ ] 3.10 Rewrite `.backtest-run-form label > span` to use `var(--card-meta-size)`, `var(--leading-meta)`, semibold, uppercase + tracking (matching `.compact-list dt`)
- [ ] 3.11 Rewrite `.backtest-run-form input` to use `var(--card-body-size)`, `var(--leading-body-card)`, `var(--font-weight-regular)`
- [ ] 3.12 Rewrite `.fetch-log-entry__time` to use `var(--font-berkeley-mono)`, `var(--card-body-size)`, `var(--leading-body-card)`, `var(--font-weight-medium)`, tabular-nums
- [ ] 3.13 Rewrite `.fetch-log-entry__meta` to use `var(--card-body-size)`, `var(--leading-body-card)`, semibold, and switch `font-family` to `var(--font-berkeley-mono)` with tabular-nums
- [ ] 3.14 Rewrite `.fetch-log-entry__error > summary` to use meta ladder (label)
- [ ] 3.15 Rewrite `.fetch-log-entry__error p` (error body) to use `var(--font-berkeley-mono)`, `var(--card-body-size)`, `var(--leading-body-card)`, regular weight
- [ ] 3.16 Rewrite `.etf-row-symbol` to use `var(--card-body-size)`, `var(--leading-body-card)`, `var(--font-weight-medium)`, `var(--font-berkeley-mono)`, tabular-nums
- [ ] 3.17 Rewrite `.etf-row-name` and `.etf-row-dot` to use `var(--card-body-size)`, `var(--leading-body-card)`
- [ ] 3.18 Rewrite `.operation-summary strong` and `.operation-link strong` to use `var(--card-body-size)`, `var(--leading-body-card)`, `var(--tracking-numeral)`
- [ ] 3.19 Add `font-family: var(--font-display)` to `.page-heading h1` rule
- [ ] 3.20 Add `font-feature-settings: "tnum", "zero"` to the JetBrains Mono `@font-face` rule in `apps/web/src/styles.css`

## 4. Delete forbidden dashboard-scope overrides

- [ ] 4.1 Remove the `.dashboard-page .compact-list dt` rule block from `apps/web/src/styles.css`
- [ ] 4.2 Remove the `.dashboard-page .compact-list dd` rule block from `apps/web/src/styles.css`
- [ ] 4.3 Remove the `.dashboard-page .metric span` rule block from `apps/web/src/styles.css`
- [ ] 4.4 Remove the `.dashboard-page .panel-primary` rule block from `apps/web/src/styles.css`
- [ ] 4.5 Verify no orphan descendant-selector override remains by grepping `grep -nE "\.dashboard-page \.(compact-list|metric|panel-primary)" apps/web/src/styles.css` (must return zero matches)

## 5. Re-wire card container padding through --card-padding-y

- [ ] 5.1 Replace `padding: var(--spacing-20);` on `.dashboard-page .dashboard-panel` with `padding: var(--card-padding-y) var(--card-padding-x);`
- [ ] 5.2 Replace `padding: var(--card-padding);` (literal 24px in some rules) / `padding: var(--spacing-16);` (on `.dashboard-panel`) with `var(--card-padding-y)` / `var(--card-padding-x)` as appropriate
- [ ] 5.3 Replace any literal px values in card padding declarations with the `--card-padding-*` tokens (verified by grep)
- [ ] 5.4 Verify `.dashboard-panel` rules in `.detail-page` and `.workflow-grid` contexts also consume `--card-padding-*`

## 6. Verification

- [ ] 6.1 Run `npm --prefix apps/web run lint:css` and fix any flagged violations (literal line-heights, descendant button selectors, lime-as-fill misuse, `:root` outside `tokens.css`, etc.)
- [ ] 6.2 Run `npm --prefix apps/web run build:tokens-doc`; commit the regenerated `docs/tokens.md`
- [ ] 6.3 Start the dev server (`npm --prefix apps/web run dev`) and visually QA the Dashboard page at viewports 375 / 768 / 1280 / 1440
- [ ] 6.4 Visually QA the Signal Detail page; confirm `.panel-primary`, `.compact-list`, `.page-heading` match Dashboard
- [ ] 6.5 Visually QA the Backtest Detail page; same cross-page parity checks
- [ ] 6.6 Open Chrome DevTools → Network panel; verify Departure Mono woff2 preloads and LCP delta is within an acceptable range (<50ms regression)
- [ ] 6.7 Run `npm --prefix apps/web run ladle` and confirm all four component stories still render without console errors
- [ ] 6.8 Verify `docs/tokens.md` reflects all new `--card-*`, `--leading-*`, `--tracking-*`, `--font-display` tokens (grep to confirm no orphan tokens)
- [ ] 6.9 Smoke-test the refresh / signal generation / backtest run loops on Dashboard to confirm no JSX regression (no styled-jsx / font-weight regressions)
