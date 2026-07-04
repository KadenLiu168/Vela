# Web Token Source

Vela keeps design tokens in more than one format. The web app currently uses one implementation source and three reference artifacts.

## Implementation Source

`apps/web/src/styles.css :root` is the current implementation token source for `apps/web`. The file is imported by `apps/web/src/main.tsx`, so the custom properties directly affect the built frontend. New web UI styling should use and update this `:root` block unless a future issue adds a token build pipeline.

The same `:root` block also declares the `@font-face` rules that load `Inter Variable` and `JetBrains Mono` from `apps/web/public/fonts/`. The stylesheet is the only place that owns the live web font binding.

## Design References

`DESIGN.md` is the visual style reference for the web frontend (Linear: midnight surfaces, acid-lime primary accent, Inter Variable + Berkeley-Mono-substitute type system).

`tokens.json` is a structured design-token reference. It is not consumed by the Vite build and does not generate CSS today.

`variables.css` is a CSS reference snapshot at the repository root. It is not imported by `apps/web`, is not linked from `apps/web/index.html`, and does not drive build output.

## Font Loading

`apps/web/index.html` preloads `/fonts/InterVariable.woff2` and removes the previous Google Fonts `<link>` and `preconnect` hints. The full `@font-face` rules (with `font-display: swap` and the system-font fallback stack) live in `apps/web/src/styles.css`.

`--font-inter-variable` is the implementation alias for the Inter Variable family (300–700) used for body, headings, navigation, buttons, and the rest of the UI.

`--font-jetbrains-mono` is the implementation alias for the chosen monospace substitute. `DESIGN.md` lists Berkeley Mono as the design intent; JetBrains Mono (OFL, free) is the loaded substitute, served by `JetBrainsMono-Regular.woff2` (weight 400) and `JetBrainsMono-Medium.woff2` (weights 500–600).

## Implementation Additions

`apps/web/src/styles.css :root` declares the Linear scale plus a small set of current implementation-only tokens that are not part of the DESIGN.md reference scale:

| Token | Value | Current role |
| --- | --- | --- |
| `--text-micro` | `11px` | Tight uppercase eyebrow labels (panel headers, table headers) |
| `--text-label` | `12px` | Detail-page `dt` metadata labels |
| `--text-body` | `15px` | Body copy (Linear's `--text-body-sm` re-pointed for direct use) |
| `--feedback-accent` | `var(--color-acid-lime)` | Default semantic feedback rail (dashboard load status) |
| `--feedback-accent-error` | `var(--color-coral-red)` | Error feedback rail (alerts, operation failures) |
| `--feedback-accent-success` | `var(--color-pulse-green)` | Success feedback rail (operation summaries) |
| `--feedback-accent-loading` | `var(--color-acid-lime)` | Loading feedback rail |
| `--feedback-accent-info` | `var(--color-signal-teal)` | Info feedback rail |
| `--feedback-accent-empty` | `var(--color-smoke)` | Empty-state feedback rail |
| `--focus-ring-color` | `var(--color-acid-lime)` | `:focus-visible` ring color |
| `--radius-cards` | `12px` | Card / panel radius alias for `--radius-xl` |
| `--radius-pills` | `9999px` | Pill / nav-pill radius alias for `--radius-full-2` |
| `--surface-slate` | `var(--color-graphite)` | Highest surface tint, ghost button fill alias |

The `--surface-void`, `--surface-carbon`, `--surface-obsidian` surface aliases are part of the Linear four-level surface stack and are not implementation additions.

Linear reserves the following type-scale and radius tokens in `:root` for future use; they are not yet referenced by component rules: `--text-body-sm`, `--text-body-lg`, `--text-heading-lg`, `--tracking-body-sm`, `--tracking-body-lg`, `--tracking-heading-lg`, `--radius-lg`, `--radius-full`, `--radius-full-2`, plus the full Linear spacing scale above `--spacing-40`.
