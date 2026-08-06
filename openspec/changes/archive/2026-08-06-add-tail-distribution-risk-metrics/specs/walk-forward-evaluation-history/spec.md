## ADDED Requirements

### Requirement: Versioned history preserves tail-distribution evidence
After `add-benchmark-regime-performance-metrics`, newly persisted Walk-forward histories SHALL store `wf_evidence_v3`, containing all valid `wf_evidence_v2` content plus per-window and aggregate strategy/fixed-benchmark distribution metrics, counts, and evidence statuses. Persistence, query, and API SHALL validate v3 strictly, continue to support valid legacy v1/v2, and reject unsupported/corrupt documents without partial output.

#### Scenario: New v3 history round-trips source-owned evidence
- **WHEN** a completed Walk-forward run with distribution metrics is persisted and queried in a fresh session
- **THEN** every v3 value, null, count, status, benchmark key, and aggregate round-trips exactly
- **AND** referenced OOS records retain matching source fields

#### Scenario: Legacy v1 and v2 remain readable
- **WHEN** a valid earlier evidence document is queried
- **THEN** all evidence defined by that version remains readable
- **AND** no distribution metric or count is fabricated

#### Scenario: Corrupt v3 fails closed
- **WHEN** v3 contains an invalid version, owner, benchmark key, count relationship, non-finite value, loss invariant, or mismatch with referenced OOS fields
- **THEN** persistence or query rejects the complete history
