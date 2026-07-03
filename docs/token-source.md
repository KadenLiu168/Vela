# Web Token Source

Vela keeps design tokens in more than one format. The web app currently uses one implementation source and two reference artifacts.

## Implementation Source

`apps/web/src/styles.css :root` is the current implementation token source for `apps/web`.

The file is imported by `apps/web/src/main.tsx`, so these custom properties directly affect the built frontend. New web UI styling should use and update this `:root` block unless a future issue adds a token build pipeline.

## Design References

`DESIGN.md` is the visual style reference for the web frontend.

`tokens.json` is a structured design-token reference. It is not consumed by the Vite build and does not generate CSS today.

`variables.css` is a CSS reference snapshot at the repository root. It is not imported by `apps/web`, is not linked from `apps/web/index.html`, and does not drive build output.

## Font Loading

`apps/web/index.html` loads Inter and Inter Tight from Google Fonts with `display=swap`.

`--font-inter` uses Inter for body copy, UI labels, captions, and metadata.

`--font-polysans` keeps `"PolySans"` first for a future self-hosted licensed font, then uses `"Inter Tight"` as the current PolySans substitute before falling back to system fonts. This adds an external Google Fonts dependency; offline or private-network environments should replace it with self-hosted `@font-face` assets in a later change.

## Implementation Additions

`apps/web/src/styles.css :root` includes current implementation-only spacing tokens that are not part of the DESIGN.md reference scale:

| Token | Value | Current role |
| --- | --- | --- |
| `--spacing-24` | `24px` | Intermediate app layout spacing |
| `--spacing-32` | `32px` | Shell and section spacing used by existing pages |

These tokens remain documented implementation additions for this baseline change. This issue does not rewrite layout spacing or remove existing page styles.
