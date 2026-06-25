## Context

COP-77 addresses the remaining formatting validation gap after COP-75 and COP-76. The repository currently passes `uv run pytest` and `uv run ruff check .`, while `uv run ruff format --check .` reports formatting drift in 15 existing Python files. Earlier archive notes already identify this as pre-existing formatting drift outside prior COP scopes.

The user decision from Explore is to accept Ruff's default formatting style in exchange for consistency and low maintenance cost.

## Goals / Non-Goals

**Goals:**

- Make `uv run ruff format --check .` pass from the repository root.
- Keep the implementation to Ruff-generated formatting changes.
- Preserve the existing passing pytest and Ruff lint gates.
- Record Ruff format validation in the existing `test-suite-validation` capability.

**Non-Goals:**

- Change Ruff formatter configuration, line length, or target version.
- Preserve manual line breaks that Ruff would collapse.
- Change runtime behavior, public APIs, data models, migrations, dependencies, or business logic.
- Rewrite historical archive notes that documented the drift.

## Decisions

1. Use Ruff default formatting output as the source of truth.

   Rationale: The repository already documents Ruff formatting commands, and accepting the formatter's default output avoids ongoing subjective formatting decisions.

   Alternative considered: tune Ruff configuration or manually preserve preferred multi-line formatting. Rejected because COP-77 is a validation cleanup issue, and changing formatter policy would expand scope.

2. Extend `test-suite-validation` rather than create a new capability.

   Rationale: COP-77 is another repository validation gate, alongside full pytest and Ruff lint validation.

   Alternative considered: create a separate formatting capability. Rejected because formatting is not a business capability and belongs with the existing validation contract.

3. Treat the code implementation as formatting-only.

   Rationale: `uv run ruff format --diff .` shows mechanical formatting changes. Keeping the patch limited to formatter output prevents unrelated behavior changes from entering a validation cleanup.

## Risks / Trade-offs

- Ruff may collapse some manually split expressions into longer single lines -> Accept because consistency and automated enforcement are the priority for this gate.
- Formatting-only diffs can make `git blame` less precise for touched lines -> Keep the change isolated in one COP and one commit so future readers can identify it as mechanical formatting.
- A future Ruff version may produce slightly different formatting -> Use the repository's locked environment through `uv` for validation.
