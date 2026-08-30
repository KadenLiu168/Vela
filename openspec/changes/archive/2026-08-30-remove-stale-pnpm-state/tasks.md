## 1. Remove obsolete pnpm state

- [x] 1.1 Inspect active documentation, scripts, CI configuration, developer instructions, and living OpenSpec material for pnpm guidance; update only references that conflict with the existing npm authority.
- [x] 1.2 Delete `apps/web/pnpm-lock.yaml` and `apps/web/pnpm-workspace.yaml`, then verify both are absent and `apps/web/package-lock.json` has no content changes.

## 2. Verify the existing npm workflow

- [x] 2.1 Run `npm --prefix apps/web ci` and confirm the clean installation does not change `apps/web/package-lock.json`.
- [x] 2.2 Run `npm --prefix apps/web run lint`, `lint:css`, `typecheck`, `test`, and `build`.
- [x] 2.3 Run `npm --prefix apps/web run check:bundle` against the production build.
- [x] 2.4 Recheck active operational surfaces for conflicting pnpm guidance and inspect the final diff to confirm no runtime, dependency-resolution, CI redesign, archived-history, or ECO-56 changes entered scope.
