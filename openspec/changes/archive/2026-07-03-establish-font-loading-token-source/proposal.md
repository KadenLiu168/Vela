## Why

The web frontend has DESIGN.md typography tokens wired into CSS, but the referenced Inter and PolySans families do not have a loading source, so the rendered app falls back to system fonts. The repository also keeps `tokens.json` and `variables.css` as design references without clear boundaries, making it easy to edit the wrong token source before later UI refinement work.

## What Changes

- Load Inter for body/UI text and a PolySans substitute for headings without blocking first paint.
- Update the PolySans font stack so future self-hosted PolySans remains the first priority while the current implementation uses an explicit substitute.
- Document that `apps/web/src/styles.css :root` is the current implementation token source.
- Mark `tokens.json` and `variables.css` as design reference artifacts that do not directly drive the web build.
- Keep the change limited to visual foundation wiring and documentation; no page UI restructure is included.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add requirements for frontend font loading, PolySans substitution, and token source documentation.

## Impact

- Affected files: `apps/web/index.html`, `apps/web/src/styles.css`, `variables.css`, and token documentation under `docs/`.
- Adds an external Google Fonts dependency for Inter and Inter Tight, with `display=swap` to avoid FOIT.
- Does not change frontend routes, API calls, DOM structure, or backend behavior.
