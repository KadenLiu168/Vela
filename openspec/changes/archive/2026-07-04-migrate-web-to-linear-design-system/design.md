## Context

The repository already has a design reference (`DESIGN.md`),
structured tokens (`tokens.json`), and a CSS custom-property
snapshot (`variables.css`) for the Ventriloc visual system. The
previous change
`2026-07-03-wire-design-tokens-into-web-css` wired those tokens
into `apps/web/src/styles.css`, where the global styling
currently lives.

Three new files — `DESIGN_Linear.md`, `tokens_Linear.json`,
`variables_Linear.css` — represent a different design system
(dark, midnight, Inter Variable, Berkeley Mono substitute). The
two systems diverge on theme polarity, accent role, type
family, density, corner geometry, and shadow vocabulary, and
several tokens share names but carry different semantic roles
(for example, `--color-graphite` means "primary text" in
Ventriloc but "subtle border" in Linear).

## Goals / Non-Goals

**Goals:**

- Replace the Ventriloc design system with the Linear design
  system across reference files and the web app's global
  stylesheet.
- Adopt Linear semantic names everywhere (no alias tricks),
  including for the 136 in-file references.
- Move font loading to self-hosted Inter Variable + JetBrains
  Mono (Berkeley Mono substitute from `DESIGN_Linear.md`).
- Keep the change visually verifiable: each existing page
  should still render with sensible contrast, focus rings, and
  feedback states under the new tokens.
- Preserve route structure, component DOM, API calls, data
  fetching, and the existing `FeedbackMessage` status roles.

**Non-Goals:**

- No light/dark theme switcher or `data-theme` toggle.
- No token build pipeline, Style Dictionary, or PostCSS
  transform.
- No new dependency, component library, icon set, or charting
  library.
- No marketing hero, landing page, or production language
  changes.
- No changes to API contracts, data models, or backend code.
- No `.tsx` / `.ts` file edits.

## Decisions

1. Adopt Linear semantic names everywhere, including consumers.
   - Alternative: keep Ventriloc names in consumer sites and
     remap only `:root` values.
   - Rationale: the user explicitly chose "全量重命名".
     Preserving Ventriloc names with new values creates
     misleading aliases and blocks future Linear-only
     contributions (e.g. shadow tokens).

2. Drop the asymmetric card radius
   (`--radius-asymmetric-card: 6px 0 0`).
   - Alternative: keep it for legacy visual parity.
   - Rationale: Linear has no equivalent; carrying a
     one-off radius is technical debt that buys nothing
     visually.

3. Use JetBrains Mono (free, Google Fonts) as the
   Berkeley Mono substitute.
   - Alternative: pay for Berkeley Mono license.
   - Rationale: Berkeley Mono is commercial (~USD 200–300);
     JetBrains Mono is the substitute listed in
     `DESIGN_Linear.md` itself and is free under OFL.

4. Self-host woff2 files in `apps/web/public/fonts/`.
   - Alternative: keep Google Fonts CDN, or use a self-hosted
     CDN mirror.
   - Rationale: user chose self-hosting; reduces external
     dependency, enables `<link rel="preload">`, keeps the
     font swap behavior visible in DevTools.

5. Preserve the three Ventriloc-only typography tokens
   (`--text-micro`, `--text-label`, `--text-body`) but
   re-point them to Linear semantic sources.
   - Alternative: delete them and refactor component CSS.
   - Rationale: those names are already consumed by
     `.app-api-meta`, `.app-nav-link`, and the dashboard
     content area; deleting them would force `.tsx` changes,
     which we want to avoid.

6. Introduce Linear's 8 shadow tokens into `:root` and apply
   `--shadow-subtle-4` to elevated cards and `--shadow-md`
   to the floating nav container.
   - Alternative: ship shadows unused, defer adoption.
   - Rationale: Linear's design language relies on hairline
     shadow + hairline border; leaving shadows out would
     produce flat surfaces that don't match the reference.

## Risks / Trade-offs

- 136 reference remappings can introduce silent contrast or
  density regressions -> mitigate by doing the swap
  top-to-bottom in `styles.css` and running the visual QA
  checklist from the proposal after each major section
  (colors, type, layout, radius, shadow).
- Linear is dark-first; users on light systems may prefer
  light -> out of scope; no light theme is delivered.
- JetBrains Mono and Inter Variable have different x-heights
  than Berkeley Mono and Inter Tight -> the 12px and 14px
  monospace UI text (issue IDs, keyboard shortcuts) may
  shift slightly in width. Visual QA at 12/14px is required
  before sign-off.
- The change touches the global stylesheet only; any
  component that relied on the Ventriloc warm-gray
  backgrounds (e.g. `app-nav` ash pill) will look
  fundamentally different. This is intended.
- Self-hosting fonts means the repo carries ~280KB of
  woff2 binary; this is acceptable but should be added to
  `.gitignore` carve-outs if it bloats the repo later.
