# Browser acceptance workflow — how to run from a clean checkout

This document explains the repository-owned, executable browser workflow for
the `web-frontend-app` capability's acceptance requirement ("Visual acceptance
is reproducible and isolated from persistent data"). Everything runs against a
production build served by a dedicated static server with **no API proxy and
no backend**; all `/api` traffic is intercepted by in-memory fixtures.

## One-time setup (clean checkout)

```bash
cd apps/web
npm ci                       # installs dependencies incl. @playwright/test
npx playwright install chromium   # downloads the Playwright browser (once)
```

If the Chromium download is unavailable, the harness can use a system Chrome:

```bash
# e2e/support uses Playwright's bundled chromium by default; to run against
# Google Chrome instead, export the channel before running tests:
PLAYWRIGHT_... npx playwright test --browser chromium   # default
```

(Using the bundled Chromium is the documented path; the browser version is
recorded in every evidence report.)

## Runs

| Command | Purpose |
| --- | --- |
| `npm --prefix apps/web run test:e2e` | Full acceptance suite (isolation, tokens, typography, spacing, surfaces, controls, responsive, viewport, motion, a11y/axe, tables/charts, reflow, matrix). Builds the production bundle with the relative `/api` base URL, serves it without the proxy, runs Playwright, and tears the server down. |
| `npm --prefix apps/web run test:e2e:baseline` | Pre-change visual baseline (only when `VELA_E2E_BASELINE=1`; writes to the Change evidence `browser/baseline/` directory). |
| `node e2e/runner.mjs` | Start the acceptance server manually (build + static preview on `127.0.0.1:4174`, proxy disabled). |

## Isolation guarantees (automatically enforced)

- The runner refuses to start when `VITE_API_BASE_URL` is set.
- Every browser request is intercepted at the context level:
  - `/api` requests must match an explicit method/path/query fixture;
    unmatched requests are aborted and fail the run afterwards.
  - Any other origin (including other local ports such as `127.0.0.1:8000`)
    is blocked before leaving the browser.
- Service workers are blocked twice (context option + init script), so a
  worker cannot bypass interception.
- The Post operation fixtures mean the tested flows issue real click events,
  but network writes land only in the in-memory simulator; no FastAPI, no
  default `vela.db`.

## Evidence layout

```text
openspec/changes/refine-web-research-visual-system/evidence/
  baseline-inventory.md          pre-change source inventory (task 1.1)
  browser/baseline/              pre-change screenshots + identity report
  browser/matrix/                acceptance matrix screenshots + report
  browser/after/                 post-change reference pages (comparison)
```

`matrix-report.json` / `baseline-report.json` record git HEAD, a dirty-source
fingerprint, the build manifest hash, the fixtures/harness fingerprint, the
browser version and per-screenshot sha256 hashes. At the end of each matrix
run, the reporter adds final Playwright statuses and errors for every test in
that run, including failures during fixture cleanup and tests that fail before
a screenshot can be captured. Generated evidence is excluded from the source
fingerprint.

## Reports

Playwright's HTML report is written to `apps/build/e2e-report/`
(`npx playwright show-report` from `apps/web`), artifacts to
`apps/build/e2e-artifacts/`.
