# Representative pages — before / after comparison (task 5.4)

Both captures come from the same executable workflow (`npm run
test:e2e:baseline` for "before", the same harness post-refinement for
"after"), against the production build with the relative `/api` base URL,
fixtures-only network isolation, chromium 153.0.8010.12.

## Dashboard — 1440x1000 (full page)

| | File | sha256 |
| --- | --- | --- |
| Before | `browser/baseline/dashboard-1440.png` | `88be7af38ae8c57ca42d0f9a3491c12fa8b4543cf058b3918f783952788e416d` |
| After | `browser/after/dashboard-1440-after.png` | `950ff0938a8a77f87468f8eb5ec415c4e5038e1fcd877a551ebe02ace4d504c1` |

Contract changes visible: research layers separated by the 48px section gap
(previously 16px), heading-to-content 24px, panel surface role (panel bg) with
emphasized metrics on raised, panels without shadow, promoted status/evidence
text (13/20), quantity columns right-aligned.

## Backtest Detail — 1440x1000 (full page)

| | File | sha256 |
| --- | --- | --- |
| Before | `browser/baseline/backtest-detail-1440.png` | `519eccd892602cbef88a2ee8e3c99a006d6f44afd16bd818f56549fa6392cf01` |
| After | `browser/after/backtest-detail-1440-after.png` | `27e60d822108ce59ed4b481b9b384e5736faca27430a1fefe66949ce13a7ced1` |

Contract changes visible: 48px section rhythm, 24px panel padding, chart
series with distinct dash patterns and synced legend swatches, comparison
matrix right-aligned value cells.

## Mobile baselines (before) and mobile matrix entries (after)

- Before: `browser/baseline/dashboard-390.png`
  (`0afd9ebf…`), `browser/baseline/backtest-detail-390.png` (`839aa5c3…`).
- After: 390px entries for all routes in `browser/matrix/`
  (`matrix-report.json` lists every entry with route/state/viewport/hash).

All hashes are also recorded in `baseline-report.json` / `matrix-report.json`
together with the version identity; the reports verify the referenced files
exist.
