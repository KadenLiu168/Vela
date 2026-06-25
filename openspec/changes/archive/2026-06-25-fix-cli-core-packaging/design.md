## Context

The repository uses a monorepo layout with the CLI under `apps/cli/src` and the reusable backend package under `packages/core/src`. The current pytest configuration adds both source roots to `pythonpath`, so tests pass, but setuptools package discovery only includes `apps/cli/src`. As a result, the installed `vela` console script can import `vela_cli` but fails when `vela_cli` imports `vela_core`.

This change is tied to Linear issue `COP-78` and addresses the gap between test-time imports and normal uv-managed command execution.

## Goals / Non-Goals

**Goals:**

- Make `uv run vela ...` work after a normal `uv sync` without manual `PYTHONPATH`.
- Keep the existing `apps/cli` and `packages/core` directory layout.
- Add verification that exercises the installed CLI entrypoint, not only direct module imports.
- Preserve the current passing pytest and Ruff checks.

**Non-Goals:**

- Do not introduce an API service, web UI, deployment workflow, or new runtime dependency.
- Do not restructure the monorepo into separately published packages.
- Do not change database schema, strategy logic, market data fetching behavior, or CLI command semantics.

## Decisions

1. Use packaging configuration to include both source roots.

   Rationale: The failure is caused by installation metadata, not by runtime business logic. Updating package discovery is the smallest fix that aligns installed behavior with test behavior.

   Alternative considered: Require developers to run commands with `PYTHONPATH=packages/core/src`. This is rejected because it makes documented commands incomplete and leaves the console script broken in a clean environment.

2. Verify the installed console script through uv.

   Rationale: Existing tests import code under pytest-controlled `pythonpath`, so they cannot catch this failure. A focused smoke check that runs `uv run vela --help` and `uv run vela init-db --database-url ...` validates the actual developer path.

   Alternative considered: Only add an import test for `vela_core`. This would be weaker because the observed failure happens through the generated console script.

3. Keep the fix local to packaging and validation.

   Rationale: The CLI and core modules already work when the core source root is visible. Changing application code would add unnecessary risk and obscure the root cause.

## Risks / Trade-offs

- Package discovery could accidentally include unintended packages if configured too broadly. Mitigation: Limit discovery to the existing source roots and verify importable packages explicitly.
- A subprocess-based CLI smoke test can be slower than unit tests. Mitigation: Keep it narrow and only exercise startup plus a temporary SQLite database initialization.
- Editable install metadata may need a fresh `uv sync` to reflect packaging changes. Mitigation: Include `uv sync` in the implementation verification steps.
