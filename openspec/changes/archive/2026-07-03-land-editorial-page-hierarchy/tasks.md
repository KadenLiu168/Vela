## 1. Explore

- [x] 1.1 Review COP-138 scope, existing OpenSpec state, UI reference notes, current stylesheet, page components, and frontend tests.
- [x] 1.2 Confirm the smallest implementation path and document automatic decisions in the change artifacts.

## 2. Implementation

- [x] 2.1 Update `apps/web/src/styles.css` so page spacing and prominent containers use `--section-gap` and `--card-padding` while dense dashboard internals stay compact.
- [x] 2.2 Update page heading styles so Dashboard uses a restrained `--text-display` hierarchy and detail pages use `--text-heading-lg` with heading weight 400.
- [x] 2.3 Apply `--radius-asymmetric-card` to the first-run guidance featured block only, without applying it to ordinary data cards.
- [x] 2.4 Verify the existing mobile media query keeps the page skeletons stacked and readable below 720px.

## 3. Validation

- [x] 3.1 Self-review the diff for blocker, major, and minor findings; fix blocker and major findings.
- [x] 3.2 Run `cd apps/web && npm run test`.
- [x] 3.3 Run `cd apps/web && npm run typecheck`.
- [x] 3.4 Run `cd apps/web && npm run build`.
- [x] 3.5 Run OpenSpec validation for `land-editorial-page-hierarchy`.
