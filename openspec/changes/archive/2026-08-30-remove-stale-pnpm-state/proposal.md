## Why

Vela Web already uses npm and `apps/web/package-lock.json` as its sole operational package-management path, but two stale pnpm files still imply a second source of dependency state. Removing that ambiguity now provides a low-risk prerequisite for ECO-56 without changing product or build behavior.

## What Changes

- Remove `apps/web/pnpm-lock.yaml` and `apps/web/pnpm-workspace.yaml`.
- Review active documentation, scripts, CI configuration, developer instructions, and living OpenSpec material; correct only references that still present pnpm as operational.
- Preserve the existing npm commands, CI workflow, bundle validation, and `apps/web/package-lock.json` without dependency-resolution churn.
- Leave historical/archive material and non-authoritative references unchanged.

## Capabilities

### New Capabilities

None. This is repository/tooling state cleanup and introduces no behavior.

### Modified Capabilities

None. Existing requirements already define the npm workflow, so this change opts out of delta specs with `skip_specs: true`.

## Impact

The change is limited to obsolete package-manager files and any genuinely conflicting active references discovered during implementation. It does not affect dependencies, runtime architecture, APIs, frontend behavior, Python code, domain models, database state, CI design, or later ECO cleanup work.
