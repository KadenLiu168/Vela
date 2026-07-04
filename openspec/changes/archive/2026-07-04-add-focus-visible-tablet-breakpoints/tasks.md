## 1. CSS Interaction States

- [x] 1.1 Add unified outline-based `:focus-visible` rules for links, buttons, navigation links, and inputs.
- [x] 1.2 Add restrained hover/transition feedback for enabled interactive controls without box-shadow, transform, bounce, or layout movement.
- [x] 1.3 Add `prefers-reduced-motion: reduce` rules that remove nonessential interaction transitions.

## 2. Responsive Layout

- [x] 2.1 Add intermediate Dashboard layout rules around `1024px` and `900px` for grid spans, gaps, padding, and metric density.
- [x] 2.2 Add intermediate Signal Detail and Backtest Detail layout rules for metric cards, compact metadata, equity summary, table containers, and detail page padding.
- [x] 2.3 Preserve existing `720px` mobile layout behavior and `1200px+` desktop layout behavior.

## 3. Validation

- [x] 3.1 Run `npm run test`, `npm run typecheck`, and `npm run build` in `apps/web`.
- [x] 3.2 Run available lint validation if configured.
- [x] 3.3 Run OpenSpec validation for `add-focus-visible-tablet-breakpoints`.
- [x] 3.4 Perform browser or CSS/DOM verification for representative `900px`, `1024px`, mobile, and desktop viewport behavior.
