## Why

The current web frontend was built on the Ventriloc style reference
(light, warm-paper, orange-ember accent, PolySans-only display family).
Three new files — `DESIGN_Linear.md`, `tokens_Linear.json`,
`variables_Linear.css` — establish a different standard: dark
midnight surfaces, an acid-lime primary action accent, and a single
Inter Variable family with Berkeley Mono for code-adjacent text.

Adopting the new standard requires a full theme and type swap, a
replacement of the 136 token consumers in `apps/web/src/styles.css`,
and a switch from Google Fonts to a self-hosted Inter Variable +
JetBrains Mono. No business code, route, API, or component DOM
changes are required: all styling is isolated in the global
stylesheet.

## What Changes

- Replace the `DESIGN.md` / `tokens.json` / `variables.css` trio
  with the Linear counterparts.
- Rewrite the `:root` block in `apps/web/src/styles.css` using
  Linear token names and values; rename all 136 in-file
  references to use Linear semantic names.
- Remove Ventriloc-specific tokens (Ember Orange, Brass, Ivory,
  asymmetric card radius) and introduce Linear shadow tokens.
- Update layout numbers (`--section-gap`, `--card-padding`,
  `--element-gap`) to Linear's compact density.
- Move font loading from Google Fonts (`Inter`, `Inter Tight`) to
  self-hosted Inter Variable + JetBrains Mono via `@font-face` in
  `apps/web/src/styles.css`; remove the Google Fonts `<link>` from
  `apps/web/index.html` and add a `<link rel="preload">` for the
  primary woff2.
- Update `openspec/specs/web-frontend-app/spec.md` to require
  Linear token wiring, dark surface defaults, and self-hosted
  font loading.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Adds requirements for the web frontend to
  expose the Linear design tokens through global CSS custom
  properties, render on a dark surface palette, load fonts
  self-hosted, and consume the renamed token names in styles.

## Impact

- Affected code:
  - `apps/web/src/styles.css` (rewrite `:root` + 136 references)
  - `apps/web/index.html` (remove Google Fonts, add preload)
  - `apps/web/public/fonts/` (new directory with InterVariable.woff2
    and JetBrainsMono-Regular.woff2)
- Affected reference docs:
  - `DESIGN.md`, `tokens.json`, `variables.css` (replaced by
    Linear versions)
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via
  this change's delta spec.
- Validation: existing frontend lint, typecheck, test, build
  scripts, plus OpenSpec validation, plus a manual visual QA
  pass against `DESIGN_Linear.md`.
- No API, route, data model, shared client, dependency, or
  backend impact.
- No `.tsx` / `.ts` file is modified; styling remains 100%
  CSS-bound.
