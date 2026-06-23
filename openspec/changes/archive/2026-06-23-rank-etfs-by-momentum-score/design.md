## Context

Vela already calculates a weighted `MomentumScore` for one ETF at one `as_of_date`. Signal generation now needs a deterministic candidate ordering step after those individual scores exist, before later code chooses the configured Top N ETFs.

The existing score calculation intentionally returns `score=None` when current price or configured window history is missing. Ranking should preserve that meaning by excluding missing scores from eligible candidates instead of inventing fallback values.

## Goals / Non-Goals

**Goals:**

- Rank already-calculated ETF momentum scores deterministically.
- Keep ranking independent from SQLAlchemy sessions and market price queries.
- Make Top N selection a simple slice of the ranked output.
- Cover tie and missing-score behavior with focused unit tests.

**Non-Goals:**

- Do not change the weighted momentum score formula.
- Do not recalculate momentum scores inside the ranking function.
- Do not apply trend filtering, defensive fallback, or target weights.
- Do not add database schema, migration, CLI, or persistence changes.

## Decisions

1. Add a pure ranking function that consumes `MomentumScore` values.

   Rationale: momentum scoring already owns the score result type and missing-data semantics. A pure function keeps ranking easy to test and lets future signal generation compose scoring, filtering, ranking, and selection explicitly.

   Alternative considered: query ETFs and calculate scores inside a ranking workflow. That would mix ranking with data access and make this P0 larger than needed.

2. Exclude `MomentumScore` values whose `score` is `None`.

   Rationale: a missing score means the system does not have enough data to compare the ETF fairly. Excluding it prevents Top N from selecting incomplete candidates.

   Alternative considered: keep missing-score ETFs at the end. That would help diagnostics, but diagnostics can use the original score list without making missing data eligible for ranking output.

3. Sort by `score` descending, then `etf_id` ascending.

   Rationale: score descending matches momentum selection intent. `etf_id` gives a stable tie-breaker without extra ETF metadata lookups or caller-provided ordering assumptions.

   Alternative considered: tie-break by symbol. That is more human-readable, but requires joining or passing ETF identities into a ranking function that otherwise only needs scores.

4. Assign continuous 1-based ranks after filtering.

   Rationale: persisted signal positions already represent ranks as integer values, and Top N selection is easiest when ranks are consecutive over eligible candidates.

   Alternative considered: competition ranks for ties. That preserves tie groups but creates gaps and does not improve deterministic Top N selection because ties are already broken by `etf_id`.

## Risks / Trade-offs

- Missing-score ETFs are absent from ranked output, which may hide diagnostics from ranking-only callers -> Keep diagnostics available in the input `MomentumScore` list and document the exclusion behavior in tests and specs.
- `etf_id` tie-breaking is stable but not user-facing -> Accept for core ranking; presentation layers can attach symbols after selection if needed.
- A pure function does not enforce a shared `as_of_date` across inputs -> Keep the function simple and assume callers pass scores for one ranking date; tests should use one date.
