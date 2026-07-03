## 1. Tests

- [x] 1.1 Add route tests that require multi-point equity curves to render restrained Ember highlight circles.
- [x] 1.2 Add route assertions that empty and single-point equity curve states render no Ember chart highlights.

## 2. Implementation

- [x] 2.1 Reuse the existing SVG coordinate logic for both the Brass equity curve path and selected highlight coordinates.
- [x] 2.2 Render deduped Ember highlight circles only for multi-point equity curves while preserving `data-testid="equity-curve-line"`.
- [x] 2.3 Add CSS for small Ember chart highlight circles using `--color-ember-orange`.

## 3. Validation

- [x] 3.1 Run the targeted frontend test in red/green order while implementing.
- [x] 3.2 Run `cd apps/web && npm run test`.
- [x] 3.3 Run `cd apps/web && npm run typecheck`.
- [x] 3.4 Run `cd apps/web && npm run build`.
- [x] 3.5 Run OpenSpec validation for `add-equity-curve-ember-highlights`.
