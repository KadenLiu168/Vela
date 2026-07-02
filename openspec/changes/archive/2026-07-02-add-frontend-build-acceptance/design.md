## Context

`apps/web/package.json` already exposes `typecheck` and `build` scripts. The build script runs `tsc -b && vite build`, and the current baseline passes without starting the local FastAPI service or any mock service. Existing documentation lists the commands, but the OpenSpec validation contract does not explicitly identify frontend build acceptance as a required validation path.

## Goals / Non-Goals

**Goals:**

- Treat `npm --prefix apps/web run typecheck` as an explicit acceptance command.
- Treat `npm --prefix apps/web run build` as an explicit acceptance command.
- Document that build/typecheck validation does not require the local API service, seeded SQLite data, or frontend mock/integration services.
- Keep the change limited to validation/spec/documentation for COP-122.

**Non-Goals:**

- Do not add new runtime frontend behavior.
- Do not change API endpoints, backend workflows, database models, or migrations.
- Do not add CI infrastructure or external services.
- Do not change the API integration test preparation flow introduced by earlier COPs.

## Decisions

1. Reuse the existing `build` and `typecheck` npm scripts.
   - Rationale: The current scripts already express the desired acceptance checks. Adding wrapper scripts would duplicate command paths without improving coverage.
   - Alternative considered: Add a new `validate:build` script. Rejected because `build` already includes TypeScript project build plus Vite production build, and the issue acceptance criteria names build/typecheck rather than a new command.

2. Extend `test-suite-validation` and `web-frontend-app` instead of creating a new capability.
   - Rationale: COP-122 is about validation acceptance for an existing frontend app, not a new product capability.
   - Alternative considered: Create `frontend-build-validation`. Rejected because it would fragment validation requirements that already live under `test-suite-validation`.

3. Keep implementation to documentation and OpenSpec requirements unless validation exposes an actual build/typecheck failure.
   - Rationale: Baseline commands already pass, so production code edits would be speculative.
   - Alternative considered: Change frontend source solely to create a code diff. Rejected because it would not trace to the issue's acceptance criteria.

## Risks / Trade-offs

- Build command can still pass while runtime API calls fail after deployment -> Mitigation: This COP only covers build acceptance; API integration validation remains covered by existing test paths.
- Documentation-only implementation may look light -> Mitigation: The acceptance criteria are command-based, and both commands are executed during validation.
