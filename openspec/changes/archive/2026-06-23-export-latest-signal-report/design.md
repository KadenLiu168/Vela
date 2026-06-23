## Context

The core package can generate strategy signals and persist successful or failed signal runs. The CLI can already generate a signal, but there is no command that reads the latest persisted successful signal and presents it as a reviewable report.

COP-54 needs a small reporting path on top of the existing persistence model. The report should use stored signal data instead of recalculating strategy output.

## Goals / Non-Goals

**Goals:**
- Load the latest successful persisted strategy signal for a config version, optionally constrained by signal date.
- Produce a deterministic human-readable text report with signal metadata and position rows.
- Show fallback state clearly at both report and position level.
- Expose the report through the existing CLI with stdout output and optional file export.

**Non-Goals:**
- Do not change signal generation, ranking, fallback, or persistence behavior.
- Do not add database columns or migrations.
- Do not introduce HTML, CSV, JSON, web UI, or broker integration.
- Do not implement report scheduling or email delivery.

## Decisions

- Add a core reporting module rather than formatting directly in the CLI.
  - Rationale: CLI stays thin and report formatting remains testable without command-line plumbing.
  - Alternative considered: format from `apps/cli` only. Rejected because it would duplicate database and formatting rules outside core.

- Infer fallback from persisted position data where `rank` and `score` are both absent.
  - Rationale: COP-51/53 persist defensive fallback positions with no rank or score and full target weight; no schema change is needed.
  - Alternative considered: add an explicit fallback column. Rejected because COP-54 does not require a migration and existing data already carries the signal.

- Default to latest successful signal for the loaded config version, with optional `--signal-date`.
  - Rationale: "latest signal report" should not require the user to know the latest signal date, while still allowing date-specific exports.
  - Alternative considered: require `--signal-date`. Rejected because that makes the default export less useful.

- Write plain text to stdout by default and to `--output` when requested.
  - Rationale: This satisfies human-readable export with minimal dependencies and predictable CLI behavior.
  - Alternative considered: always require an output file. Rejected because stdout supports inspection and shell redirection.

## Risks / Trade-offs

- Fallback inference relies on persisted rank/score semantics -> Mitigated with focused tests for defensive fallback rows.
- Latest signal selection could surprise users when multiple config versions exist -> Mitigated by loading the strategy config and querying only that config version.
- Plain text is not machine-oriented -> Accepted for COP-54 because the issue explicitly asks for a human-readable report.
