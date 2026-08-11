## 1. Router foundation and red tests

- [x] 1.1 Add the React Router browser dependency to `apps/web/package.json` and update only its npm lockfile resolution.
- [x] 1.2 Establish Router-aware test rendering for `App` and directly tested page components without changing their API mocks or unrelated assertions.
- [x] 1.3 Add focused failing application-route tests for the declared route map, browser Back/Forward behavior, malformed numeric identifiers, unmatched paths, and the explicit not-found page.
- [x] 1.4 Add a focused failing interaction test proving that a Dashboard backtest-date form survives an internal detail transition and return within one mounted application session.

## 2. Declarative route ownership

- [x] 2.1 Compose a `BrowserRouter` around the application content and replace App-owned pathname state, `pushState`, `popstate`, regular-expression dispatch, and Dashboard fallback with a declarative route tree for all eight existing path forms plus a catch-all route.
- [x] 2.2 Add minimal route adapters that obtain dynamic identifiers from Router parameters, preserve the existing decimal-digit acceptance boundary, and render the not-found page without mounting a detail page for malformed values.
- [x] 2.3 Keep Dashboard backtest form state above `Routes`; retain module-level lazy page imports, the existing Suspense fallback, and a location-keyed route error boundary so loading and rejected-chunk recovery preserve AppShell.
- [x] 2.4 Implement the explicit not-found page inside AppShell with one page-level heading and a Router link to Dashboard.

## 3. Unify navigation and search ownership

- [x] 3.1 Convert AppShell primary navigation to Router `NavLink` entries, preserving current-route accessibility and existing active-link styling on list and detail paths.
- [x] 3.2 Convert every production internal detail anchor in Dashboard, Signal list/detail, Backtest list/detail, and Walk-forward list/detail pages to Router `Link` without changing labels, routes, or external-link behavior.
- [x] 3.3 Pass Router programmatic navigation to the command palette and replace the Walk-forward completion helper's `window.history`/synthetic-event path with `useNavigate()`.
- [x] 3.4 Replace Signal history's `window.location` and `history.replaceState` source-filter handling with Router location/navigation while preserving valid-source filtering, offset reset, unrelated query parameters, hash, and replace semantics for invalid values.
- [x] 3.5 Remove only the manual browser-history helpers and imports made obsolete by the Router conversion; leave the route-load failure's explicit reload recovery intact.

## 4. Focused regression coverage

- [x] 4.1 Update application and route-code-splitting tests to assert Router-visible behavior rather than synthetic `popstate`, while retaining lazy-loading and route-failure recovery assertions.
- [x] 4.2 Update affected page and command-palette tests for Router context; cover Router navigation after command selection and accepted Walk-forward completion without `window.history` spies.
- [x] 4.3 Extend Signal history tests to prove Router-owned source-query normalization and preservation of unrelated query parameters and hash.
- [x] 4.4 Audit production TSX for internal native anchors and manual history/location mutations; verify none remain except the explicit route-load failure reload and non-navigation URL construction.

## 5. Validation and acceptance

- [x] 5.1 Run `openspec validate replace-manual-web-routing-with-react-router --strict` and resolve every issue.
- [x] 5.2 Run `npm --prefix apps/web ci`, then `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
- [x] 5.3 Run `npm --prefix apps/web run check:bundle` only after the fresh build; record the measured result and treat any budget failure as a separate evidence-backed decision rather than relaxing the threshold in this Change.
- [x] 5.4 Perform browser acceptance at 1440x1000 and 390x844: direct detail URL, internal detail Link with Dashboard form preservation, browser Back/Forward, command-palette navigation, accepted Walk-forward redirect, invalid-id/unknown-path 404, and route loading/failure recovery with no page-level horizontal overflow.
- [x] 5.5 Review the final diff against `web-client-routing`, existing `web-route-code-splitting`, and unaffected API/database scope; confirm no persistent `vela.db` or unrelated Change files were modified.
