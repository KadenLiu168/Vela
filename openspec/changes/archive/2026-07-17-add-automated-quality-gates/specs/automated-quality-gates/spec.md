## ADDED Requirements

### Requirement: Repository CI quality gate

The repository SHALL provide an automated CI quality gate that runs on pull requests and pushes to the main branch.

#### Scenario: Pull request validation runs automatically

- **WHEN** a pull request targets the main branch
- **THEN** CI MUST run the configured Python and frontend quality validation jobs
- **AND** CI MUST report failure if any required validation command fails

#### Scenario: Main branch push validation runs automatically

- **WHEN** a commit is pushed to the main branch
- **THEN** CI MUST run the configured Python and frontend quality validation jobs
- **AND** CI MUST report failure if any required validation command fails

### Requirement: Python CI validation

The repository SHALL provide a Python CI job that installs dependencies through `uv` and runs the required Python validation commands from the repository root.

#### Scenario: Python CI runs lint, format, type, and test checks

- **WHEN** the Python CI job executes
- **THEN** it MUST install the Python project with the dev dependency group through `uv`
- **AND** it MUST run `uv run ruff check .`
- **AND** it MUST run `uv run ruff format --check .`
- **AND** it MUST run the configured mypy validation command
- **AND** it MUST run `uv run pytest`

### Requirement: Frontend CI validation

The repository SHALL provide a frontend CI job that installs frontend dependencies and runs the required frontend validation commands from the repository root.

#### Scenario: Frontend CI runs lint, type, test, and build checks

- **WHEN** the frontend CI job executes
- **THEN** it MUST install dependencies for `apps/web`
- **AND** it MUST run `npm --prefix apps/web run lint`
- **AND** it MUST run `npm --prefix apps/web run lint:css`
- **AND** it MUST run `npm --prefix apps/web run typecheck`
- **AND** it MUST run `npm --prefix apps/web run test`
- **AND** it MUST run `npm --prefix apps/web run build`

### Requirement: Local pre-commit quality feedback

The repository SHALL provide a pre-commit configuration for fast local feedback before commits are created.

#### Scenario: Pre-commit runs fast checks

- **WHEN** a developer runs pre-commit for the repository
- **THEN** pre-commit MUST run Ruff linting with automatic fixes where safe
- **AND** pre-commit MUST run Ruff formatting
- **AND** pre-commit MUST run lightweight file hygiene checks
- **AND** pre-commit MUST NOT require the full pytest suite or frontend production build to complete before every commit

### Requirement: Mypy baseline configuration

The repository SHALL define a mypy configuration that makes static type checking executable and stable for the Python source tree.

#### Scenario: Mypy runs against Python source packages

- **WHEN** a developer or CI runs the configured mypy validation command
- **THEN** mypy MUST check the Python source trees under `apps/api/src`, `apps/cli/src`, and `packages/core/src`
- **AND** mypy MUST use Python 3.11 semantics
- **AND** mypy MUST fail on type errors in checked project code

#### Scenario: Mypy configuration avoids unbounded third-party noise

- **WHEN** mypy encounters third-party libraries without complete type information
- **THEN** the configuration MUST handle those libraries explicitly through targeted settings or dependency stubs
- **AND** the configuration MUST NOT rely on broad, undocumented suppression of all project type errors

### Requirement: Gradual lint strictness expansion

The repository SHALL support gradual expansion of Ruff lint coverage without blocking the initial CI gate on a large unrelated cleanup.

#### Scenario: Initial Ruff CI uses stable baseline rules

- **WHEN** the initial CI gate is introduced
- **THEN** Ruff MUST enforce the existing baseline lint and format checks
- **AND** security or complexity rule expansion MUST be introduced separately from the minimal CI gate if those rules reveal unrelated existing failures

#### Scenario: Test-specific security lint exceptions are explicit

- **WHEN** security lint rules are enabled for the repository
- **THEN** test-specific false positives MUST be handled with explicit `per-file-ignores` or equivalent targeted configuration
- **AND** production source files MUST remain covered by the enabled security rules

### Requirement: Branch protection alignment

The repository SHALL document that CI becomes a real merge gate only when the main branch requires the CI checks to pass before merging.

#### Scenario: Main branch protection is configured

- **WHEN** repository maintainers configure GitHub branch protection or rulesets for the main branch
- **THEN** the required CI checks MUST include the Python and frontend quality validation jobs
- **AND** pull requests MUST NOT be mergeable through the protected path while those required checks are failing
