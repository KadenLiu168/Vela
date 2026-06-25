## Why

COP-79 starts the Phase 1 frontend track by adding an independent `apps/web` entrypoint. The repository currently has backend and CLI foundations but no minimal web application that can be started or extended by later frontend issues.

## What Changes

- Add a minimal `apps/web` frontend application skeleton using Vite, React, TypeScript, and npm.
- Provide a project-level development command that can be run from the repository root: `npm --prefix apps/web run dev`.
- Document the equivalent app-local command: `cd apps/web && npm run dev`.
- Add directory structure for pages, components, API client code, and tests without implementing business UI, backend API integration, authentication, charts, routing flows, or deployment.
- Update project documentation only where needed to acknowledge the new web entrypoint.

## Capabilities

### New Capabilities

- `web-frontend-app`: Defines the minimal frontend application skeleton, development command, and extensible directory layout for future web work.

### Modified Capabilities

- None.

## Impact

- Adds Node frontend tooling under `apps/web` only, including `package.json`, npm lockfile, Vite, TypeScript, and test configuration.
- Adds minimal React source and test files under `apps/web/src`.
- Adds documentation for web app setup and commands.
- Does not introduce a root Node workspace, root `package.json`, or frontend business features.
