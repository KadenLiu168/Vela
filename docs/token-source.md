# Web Token Source

Vela keeps design tokens in **one** file for the web frontend:
`apps/web/src/styles/tokens.css`. That file is the canonical,
on-disk source of every CSS custom property the web app uses as a
design token; it is imported by `apps/web/src/styles.css` and is
the only place under `apps/web/src/` allowed to declare a
`:root { ... }` block (see the `design-system` OpenSpec capability
at `openspec/specs/design-system/`).

## Implementation source

`apps/web/src/styles/tokens.css` is the implementation source. It is
imported into `apps/web/src/styles.css` via
`@import "./styles/tokens.css";` at the top of the stylesheet; Vite
inlines it into the built bundle. New web UI styling MUST consume
tokens by referencing `var(--<token-name>)` and MUST NOT declare
new CSS custom properties anywhere under `apps/web/src/`.

## Font loading

`apps/web/src/styles.css` holds the `@font-face` declarations that
load `Inter Variable` and `JetBrains Mono` from
`apps/web/public/fonts/`. The monospace family token
(`--font-berkeley-mono`) chains the value
`'JetBrains Mono', 'Berkeley Mono', ui-monospace, ...` so the served
woff2 actually renders today; the token name keeps the design intent
(Berkeley Mono) so a future swap of the served font needs only one
line of CSS.

The same `apps/web/src/styles.css` file holds the page-level
declarations for `background`, `color`, `font-family`, and
`color-scheme: dark` on `body`. Those are application-level rules,
not token declarations.

## Token groups declared in `tokens.css`

Colors (`--color-*`), Surfaces (`--surface-*`), Font families
(`--font-*`), Typography scale (`--text-*`, `--leading-*`,
`--tracking-*`), Font weights (`--font-weight-*`), Spacing
(`--spacing-*`), Layout (`--page-max-width`, `--section-gap`,
`--card-padding`, `--element-gap`), Border radius (`--radius-*`),
Shadow (`--shadow-*`), Feedback accents (`--feedback-accent-*`,
`--focus-ring-color`), Motion (`--duration-*`, `--ease-out`). The
file's leading comment block lists the same groups.

## Why this changed

Before this change, the design-token references for the web
frontend were scattered: `DESIGN.md` and `tokens.json` (both
deleted) were style guides, `/variables.css` was an unimported CSS
snapshot, and `apps/web/src/styles.css` had its own `:root { ... }`
block that drifted from those references. The drift caused today's
half-applied font rename and was the kind of bug a future change
must route through an OpenSpec proposal. The `design-system`
capability closes that loop.
