## Context

`DESIGN.md` defines PolySans for headings and Inter for body/UI text. `apps/web/src/styles.css` already exposes `--font-polysans` and `--font-inter`, but `apps/web/index.html` does not load either family and the repository contains no local font files, so both stacks fall through to system fonts.

The repository also contains three token representations: `apps/web/src/styles.css :root`, `tokens.json`, and `variables.css`. Only `styles.css` is imported by `apps/web/src/main.tsx`, so it is the active implementation source. `tokens.json` and `variables.css` remain useful design references but are not build inputs.

## Goals / Non-Goals

**Goals:**

- Provide a concrete Inter loading source for body and UI typography.
- Provide a PolySans substitute strategy that keeps future self-hosted PolySans first in the stack.
- Avoid FOIT by using a swap-based font loading path and CSS fallback stacks.
- Document the token source boundary so later UI changes edit `apps/web/src/styles.css :root`.

**Non-Goals:**

- Do not self-host PolySans or add font binary assets in this change.
- Do not delete `variables.css`.
- Do not introduce a token build pipeline.
- Do not restyle pages, change DOM structure, or alter frontend behavior.

## Decisions

1. Use Google Fonts for Inter and Inter Tight.
   - Rationale: the repo has no font assets, and this is the smallest way to make Inter render predictably without adding package dependencies or a local asset pipeline.
   - Alternative considered: self-host fonts. Rejected for this issue because no licensed PolySans files or local font source are present.

2. Use Inter Tight as the current PolySans substitute.
   - Rationale: `DESIGN.md` names Inter Tight as the preferred substitute. The CSS stack will remain `"PolySans", "Inter Tight", "Space Grotesk", ...` so adding self-hosted PolySans later automatically takes precedence.
   - Alternative considered: use Space Grotesk only. Rejected because it is the backup substitute, not the preferred substitute in `DESIGN.md`.

3. Load fonts in `index.html` with preconnect and `display=swap`.
   - Rationale: `display=swap` avoids invisible text during font load, while preconnect reduces Google Fonts connection cost.
   - Alternative considered: CSS `@import`. Rejected because HTML links are clearer and avoid delaying CSS parsing.

4. Treat `apps/web/src/styles.css :root` as the implementation token source.
   - Rationale: it is the only token definition imported by the app build today.
   - Alternative considered: import `variables.css` or generate CSS from `tokens.json`. Rejected because that would add implementation surface beyond the visual baseline requested here.

## Risks / Trade-offs

- External Google Fonts dependency can fail or be unavailable offline -> system fallbacks remain in both stacks, and the dependency is documented for a future self-hosting issue.
- Inter Tight is not PolySans -> the font stack keeps PolySans first so a future licensed self-hosted font can replace the substitute without changing call sites.
- Token references can still drift manually -> `variables.css` and a docs page will mark reference-only status, reducing accidental edits to non-build files.

## Migration Plan

1. Add Google Fonts links for Inter and Inter Tight to `apps/web/index.html`.
2. Update `apps/web/src/styles.css :root` comments and font stacks.
3. Add reference-only comments to `variables.css`.
4. Add token source documentation under `docs/`.
5. Run OpenSpec validation and frontend test/typecheck/build commands.

## Open Questions

None.
