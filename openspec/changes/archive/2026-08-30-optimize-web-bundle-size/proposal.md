## Why

The current npm-locked production build succeeds, but `check:bundle` fails because lazy-route JavaScript is 77,211 raw bytes and total JavaScript is 346,363 raw bytes, above the implemented 70,000 and 340,000 ceilings. The overage followed Backtest and Walk-forward detail growth rather than dependency or build-identity drift, so it needs an independent, evidence-led optimization Change instead of being folded into `remove-stale-pnpm-state`.

## What Changes

- Extend bundle evidence to attribute raw bytes to every lazy route entry and its asynchronous shared chunks before selecting an optimization.
- Reduce emitted JavaScript through measured removal of duplicate or unnecessary code and valid chunk boundaries, targeting lazy-route JavaScript at or below 70,000 raw bytes with regression margin; retain only changes that also reduce total JavaScript.
- Preserve the seven React Router lazy routes, eager runtime/application ownership, build identity, user-visible behavior, and the npm lockfile.
- Reconcile the living bundle specification's stale 61,000/333,000 figures with the already implemented, redesign-evidenced 70,000/340,000 ceilings; any further increase requires separate evidence and explicit artifact review.
- Keep `remove-stale-pnpm-state` and ECO-56 out of scope.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-route-code-splitting`: Require route-by-route size attribution during remediation and align the living contract with the existing identity-pinned 70,000-byte lazy and 340,000-byte total JavaScript gates while preserving all route ownership and runtime identity checks.

## Impact

- Expected implementation scope: `apps/web/scripts/bundle-manifest.mjs`, its focused tests, and only evidence-proven modules under `apps/web/src/pages/` or existing shared frontend helpers needed to remove duplicate JavaScript.
- `apps/web/scripts/check-bundle.mjs` may gain reporting only; its 70,000/340,000 ceilings must not increase.
- No public route, API, database, financial calculation, visual behavior, dependency, `apps/web/package-lock.json`, `remove-stale-pnpm-state`, or ECO-56 change.
