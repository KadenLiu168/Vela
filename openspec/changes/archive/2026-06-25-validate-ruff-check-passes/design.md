## Context

The repository already uses Ruff as the configured linting tool through `pyproject.toml`. COP-76 is an acceptance-gate change: `uv run ruff check .` must pass from the repository root.

## Goals / Non-Goals

**Goals:**

- Verify the current repository passes `uv run ruff check .`.
- Document Ruff lint validation as part of the existing repository-level validation capability.

**Non-Goals:**

- Do not change runtime behavior, public APIs, data models, migrations, or dependencies.
- Do not include formatting-only cleanup from `uv run ruff format --check .`.

## Decisions

- Extend `test-suite-validation` instead of creating a new capability, because COP-76 concerns repository validation rather than a business feature.
- Keep implementation minimal: if Ruff lint already passes, only OpenSpec artifacts and archive updates are required.

## Risks / Trade-offs

- Existing formatting issues may still be reported by `ruff format --check`, but COP-76 only covers `ruff check`; keep formatting cleanup out of this commit unless required by lint.
