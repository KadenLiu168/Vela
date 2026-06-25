## Context

Vela currently has backend, CLI, and OpenSpec foundations, but no frontend application entrypoint. COP-79 introduces the first frontend skeleton for Phase 1 while keeping it independent from backend business logic and avoiding a repository-wide Node workspace decision.

## Goals / Non-Goals

**Goals:**

- Create `apps/web` as a minimal Vite React TypeScript application.
- Use npm locally within `apps/web`.
- Support a root-level development command: `npm --prefix apps/web run dev`.
- Include source directories that can hold pages, components, API client code, and tests.
- Provide basic frontend validation commands for tests, linting, type checking, and build.

**Non-Goals:**

- Do not add a root `package.json`, `pnpm-workspace.yaml`, or monorepo Node workspace.
- Do not implement business pages, ETF data display, charts, authentication, routing flows, backend API integration, or deployment.
- Do not change backend Python package behavior.

## Decisions

- Use Vite + React + TypeScript + npm for `apps/web`.
  - This satisfies the minimal runnable app requirement without imposing Next.js or a root Node workspace.
  - Alternative considered: pnpm workspace. Rejected for this COP because it adds root-level package management decisions outside the skeleton boundary.
  - Alternative considered: Next.js. Rejected for this COP because the issue only requires an independent frontend entrypoint, not SSR or framework-level routing decisions.
- Keep the project command root-runnable with `npm --prefix apps/web run dev`.
  - This matches the repository habit of running common commands from the root while keeping Node configuration scoped to `apps/web`.
  - The app-local equivalent `cd apps/web && npm run dev` will be documented for convenience.
- Use lightweight placeholder structure and tests.
  - The skeleton will include pages, components, API client, and test directories, but placeholders must avoid business functionality that belongs to later COP issues.

## Risks / Trade-offs

- npm may need migration if the repository later standardizes on pnpm workspaces -> Keep all Node package files under `apps/web` so migration remains localized.
- Vite app defaults may be too minimal for future routing needs -> Leave routing decisions to later frontend issues and keep the current page structure simple.
- README Phase 1 wording currently says Web UI is out of scope -> Update documentation narrowly to acknowledge the new frontend skeleton without claiming completed business UI.
