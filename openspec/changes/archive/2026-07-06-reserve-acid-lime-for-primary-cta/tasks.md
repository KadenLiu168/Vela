## 1. Nav-link active-state CSS

- [x] 1.1 In `apps/web/src/styles.css`, replace the body of
      `.app-nav-link[aria-current="page"]` (currently at
      line 137) with:
      ```
      color: var(--color-paper);
      ```
      and a new rule beneath that uses
      `box-shadow: inset 0 -2px 0 0 var(--color-acid-lime);`
      on the same selector
- [x] 1.2 Update the `:hover` rule beneath it to
      `color: var(--color-bone);` and remove any background
      override

## 2. Component-side verification

- [x] 2.1 Confirm `AppShell.tsx` preserves the
      `aria-current="page"` attribute on the active nav-link
      (this attribute already exists; no change expected)
- [x] 2.2 Confirm no `style` override on the active nav-link

## 3. Validation

- [x] 3.1 `openspec validate reserve-acid-lime-for-primary-cta`
      passes
- [x] 3.2 `npm --prefix apps/web run typecheck` passes
- [x] 3.3 `npm --prefix apps/web run lint` passes
- [x] 3.4 `npm --prefix apps/web run test` passes
- [x] 3.5 `npm --prefix apps/web run build` passes
- [x] 3.6 `uv run pytest -q` passes
- [x] 3.7 DevTools visual QA on `/`, `/signals/:id`,
      `/backtests/:id`: the active nav-link on every route
      shows paper text + a 2px lime underline, never a lime
      fill

      Known gap (deferred to `unify-buttons-into-three-variants`
      which lands next): the Dashboard Operations panel
      currently renders three acid-lime filled buttons
      (Fetch market data, Generate signal, Bootstrap) because
      `.operation-list button` styles all three together.
      After change 2 lands, Bootstrap will be the only lime
      fill on the Dashboard, satisfying the
      `design-system` reservation rule in full. The DevTools
      QA for THIS change confirms only the nav-link side.
- [x] 3.8 `openspec-archive-change reserve-acid-lime-for-primary-cta`
