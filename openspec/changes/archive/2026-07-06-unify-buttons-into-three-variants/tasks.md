## 1. Variant CSS

- [x] 1.1 Add `.button-primary`, `.button-secondary`,
      `.button-tertiary` rules to `apps/web/src/styles.css`,
      reading only tokens from `tokens.css`
- [x] 1.2 Delete `.operation-list button { ... }` rule (and any
      descendant-selector button rule); port its `:hover`,
      `:disabled`, and `prefers-reduced-motion` overrides onto
      the variant classes

## 2. Audit existing buttons

- [x] 2.1 List every `<button>` and `[role="button"]` in
      `apps/web/src/` and record its current className
- [x] 2.2 Map each to one of the three variants per the spec
      contract (primary = the unique most-important action per
      view; secondary = outlined alternative; tertiary = text-only
      link-style action)

## 3. Refactor classNames

- [x] 3.1 In `DashboardPage.tsx` Operations panel:
      - Bootstrap → add `button-primary`
      - Fetch market data → add `button-secondary`
      - Generate signal → add `button-secondary`
- [x] 3.2 In `DashboardPage.tsx` heading refresh:
      - drop `dashboard-refresh-action` styling class; add
        `button-secondary`
- [x] 3.3 In `EmptyAction` component (or its call sites):
      attach `button-secondary`
- [x] 3.4 In `FeedbackMessage`, `FirstRunGuidance`,
      `BacktestRunForm`, and any remaining `.tsx` files: convert
      each `<button>` to use a variant className; keep any
      existing semantic className alongside

## 4. Validation

- [x] 4.1 `openspec validate unify-buttons-into-three-variants`
      passes (note: no spec delta, but proposal/design/tasks
      must still parse)
- [x] 4.2 `npm --prefix apps/web run typecheck` passes
- [x] 4.3 `npm --prefix apps/web run lint` passes
- [x] 4.4 `npm --prefix apps/web run test` passes
- [x] 4.5 `npm --prefix apps/web run build` passes
- [x] 4.6 `uv run pytest -q` passes (no backend effect but
      confirm)
- [x] 4.7 `grep -nE "\\.operation-list button|\\.app-nav button|button:has" apps/web/src/styles.css`
      returns no descendant-selector button leaks
- [x] 4.8 Visual QA: Dashboard now shows exactly one acid-lime
      filled button (Bootstrap); other actions are outlined
- [x] 4.9 `openspec-archive-change unify-buttons-into-three-variants`
