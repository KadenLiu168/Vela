## 1. Baseline verification

- [x] 1.1 Confirm current repository state for `.github/`, `.pre-commit-config.yaml`, mypy configuration, Ruff configuration, and frontend package scripts.
- [x] 1.2 Run the existing Python checks (`uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`) and record whether failures are pre-existing baseline issues.
- [x] 1.3 Run the existing frontend checks (`npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, `npm --prefix apps/web run build`) and record whether failures are pre-existing baseline issues.

## 2. Python quality configuration

- [x] 2.1 Add a `[tool.mypy]` configuration to `pyproject.toml` for Python 3.11 and the source trees under `apps/api/src`, `apps/cli/src`, and `packages/core/src`.
- [x] 2.2 Add targeted mypy handling for third-party packages that lack complete type information, avoiding broad suppression of project type errors.
- [x] 2.3 Verify the configured mypy command runs from the repository root without manually setting `PYTHONPATH`.
- [x] 2.4 Keep the existing Ruff baseline rules stable for the initial CI gate, and document security/complexity expansion as a later tightening step if it would cause unrelated cleanup.

## 3. Continuous integration

- [ ] 3.1 Create `.github/workflows/ci.yml` with triggers for pull requests targeting `main` and pushes to `main`.
- [ ] 3.2 Add a Python CI job that installs dependencies with `uv sync --group dev` and runs Ruff lint, Ruff format check, mypy, and pytest from the repository root.
- [ ] 3.3 Add a frontend CI job that installs `apps/web` dependencies and runs lint, CSS lint, typecheck, tests, and production build from the repository root.
- [ ] 3.4 Use separate Python and frontend jobs so failures identify the affected toolchain clearly.

## 4. Local pre-commit feedback

- [ ] 4.1 Add `pre-commit` to the development dependency set if it is not already available.
- [ ] 4.2 Create `.pre-commit-config.yaml` with Ruff lint autofix, Ruff format, and lightweight file hygiene hooks.
- [ ] 4.3 Exclude full pytest, mypy, and frontend build from pre-commit to keep commit-time feedback fast.
- [ ] 4.4 Document how to install and run pre-commit locally.

## 5. Documentation and branch protection

- [ ] 5.1 Document the canonical local validation commands that mirror CI.
- [ ] 5.2 Document that GitHub branch protection or rulesets must require the Python and frontend CI jobs before CI becomes a real merge gate.
- [ ] 5.3 If repository settings access is available, configure main branch protection to require the new CI checks; otherwise record it as a manual follow-up for the maintainer.

## 6. Final validation

- [ ] 6.1 Run Python quality validation from the repository root: Ruff lint, Ruff format check, configured mypy, and pytest.
- [ ] 6.2 Run frontend quality validation from the repository root: lint, CSS lint, typecheck, test, and build.
- [ ] 6.3 Validate the OpenSpec change with `openspec validate --change add-automated-quality-gates`.
- [ ] 6.4 Summarize any pre-existing baseline failures separately from failures introduced by this change.
