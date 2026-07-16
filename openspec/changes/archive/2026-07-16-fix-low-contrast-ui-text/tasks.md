## 1. Text Color Remediation

- [x] 1.1 Update `.status-pill` default text color from `--color-ash` to `--color-fog` in `apps/web/src/styles.css`.
- [x] 1.2 Update `.status-pill-neutral` so neutral status pill text uses `--color-fog` instead of the empty-state accent token.
- [x] 1.3 Update `.command-palette-input::placeholder` from `--color-ash` to `--color-fog`.
- [x] 1.4 Update `.command-palette-row-kind` from `--color-ash` to `--color-fog`.

## 2. Decorative Separator Semantics

- [x] 2.1 Keep `.etf-row-dot` visually subdued as decoration and add `aria-hidden="true"` to the ETF row dot separator in `DashboardPage.tsx`.
- [x] 2.2 Confirm that existing `--color-ash` and `--color-smoke` uses left unchanged are decorative roles such as borders, strokes, grid lines, or accents rather than readable text.

## 3. Verification

- [x] 3.1 Search `apps/web/src/` for `color: var(--color-ash)` and `color: var(--color-smoke)` and verify no remaining matches are readable text that violates the new design-system requirement.
- [x] 3.2 Run the relevant web frontend tests for dashboard and command-palette behavior.
- [x] 3.3 Run `openspec status --change "fix-low-contrast-ui-text"` and confirm the change remains apply-ready.
