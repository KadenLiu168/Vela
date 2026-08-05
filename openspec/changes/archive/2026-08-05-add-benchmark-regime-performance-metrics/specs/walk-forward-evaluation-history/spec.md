## ADDED Requirements

### Requirement: Versioned history preserves benchmark-regime evidence
Newly persisted Walk-forward histories SHALL store `wf_evidence_v2`, containing all valid `wf_evidence_v1` content plus per-benchmark daily CAPM/monthly-capture aggregates and per-window daily-session or selected-month evidence counts defined by this Change. Persistence, query, and API boundaries SHALL validate `v2` strictly, continue to support legacy `v1`, and fail closed on unsupported versions, missing benchmark ownership, or corrupt metric/count relationships.

#### Scenario: New history round-trips v2 evidence
- **WHEN** a completed Walk-forward run with benchmark-regime metrics is persisted and queried in a fresh session
- **THEN** its `wf_evidence_v2` document round-trips every new aggregate, count, null, and evidence status
- **AND** referenced OOS benchmark rows retain the matching per-window source values

#### Scenario: Legacy v1 history remains readable
- **WHEN** a valid pre-change `wf_evidence_v1` history is queried
- **THEN** existing evidence remains readable
- **AND** no CAPM or capture value is fabricated

#### Scenario: Corrupt v2 history fails closed
- **WHEN** a `wf_evidence_v2` document has an unsupported benchmark key, invalid count, non-finite value, or source ownership mismatch
- **THEN** persistence or query rejects the complete history instead of returning partial evidence
