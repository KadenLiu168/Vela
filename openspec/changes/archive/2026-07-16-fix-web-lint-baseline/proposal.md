## Why

The web frontend lint gates currently fail on `main` before unrelated changes can be committed safely. This change restores the ESLint and CSS lint baselines so future OpenSpec changes can satisfy the repository's quality gates without carrying unrelated failures.

## What Changes

- Fix existing React ESLint `react-hooks/set-state-in-effect` failures in route pages without changing user-visible behavior.
- Fix existing Stylelint baseline failures by routing literal line-height and border-radius values through existing design tokens.
- Add explicit frontend lint validation coverage to the repository validation contract.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite-validation`: Add frontend ESLint and CSS lint commands as required passing validation gates.

## Impact

- Affected code: existing web route pages with synchronous loading-state resets inside effects, and existing CSS declarations flagged by Stylelint.
- Affected validation: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`.
- No API, database, backend, dependency, or product workflow changes.
