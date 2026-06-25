## Context

COP-75 is a Phase 1 acceptance issue for confirming that the repository's configured pytest suite passes. The project already defines pytest configuration in `pyproject.toml`, and the canonical command is documented in `README.md` as `uv run pytest`.

## Goals / Non-Goals

**Goals:**

- Run the configured full pytest suite with `uv run pytest`.
- If tests fail, make only the minimal fix needed for the failing behavior.
- Validate the final repository state with pytest, existing lint/format commands, and OpenSpec validation.

**Non-Goals:**

- Add new business features.
- Refactor unrelated implementation code.
- Change public APIs, data models, migrations, dependencies, or test configuration unless required by a pytest failure.

## Decisions

- Use `uv run pytest` as the source of truth for the acceptance gate because it is the command specified by COP-75 and the repository documentation.
- Treat a passing test suite as sufficient implementation for this change because the issue's goal is validation, not feature delivery.
- Keep any potential fixes narrowly scoped to observed pytest failures to avoid mixing unrelated cleanup into COP-75.

## Risks / Trade-offs

- A currently passing suite may hide environment-specific issues -> Mitigation: also run existing lint/format and OpenSpec validation commands before commit.
- Creating an OpenSpec capability for validation adds documentation without code changes -> Mitigation: keep the capability narrow and archive it immediately after verification.
