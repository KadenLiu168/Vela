## ADDED Requirements

### Requirement: Backtest responses expose stored benchmark-regime metrics
Benchmark entries in successful run and detail responses SHALL expose nullable CAPM Alpha, Beta, R-squared, daily CAPM observation count, Monthly Up Capture, selected up-month count, Monthly Down Capture, and selected down-month count. CAPM values SHALL be non-null only for `csi_300_buy_hold`; capture values remain available for both fixed benchmarks, Decimal values SHALL remain six-place strings, and the router MUST NOT recalculate them.

#### Scenario: New detail returns exact persisted comparison values
- **WHEN** Backtest Detail loads a newly calculated benchmark-enabled run
- **THEN** both named benchmark objects return their stored monthly capture values and selected-month counts
- **AND** only the CSI 300 object returns stored proxy CAPM values and count

#### Scenario: Legacy detail retains explicit nulls
- **WHEN** Backtest Detail loads legacy benchmark rows created before this Change
- **THEN** new fields are null rather than omitted, zero-filled, or recalculated

### Requirement: Walk-forward responses expose versioned regime evidence
Walk-forward detail SHALL serialize validated `wf_evidence_v2` per-window and aggregate benchmark-regime evidence with metric-local counts and statuses, while valid legacy `wf_evidence_v1` detail remains readable without fabricated fields. OpenAPI SHALL describe both supported evidence shapes unambiguously.

#### Scenario: V2 detail preserves evidence semantics
- **WHEN** a client requests a valid `wf_evidence_v2` history
- **THEN** the response returns named proxy/monthly-capture metrics, daily-session and selected-month evidence counts, aggregate counts, and statuses unchanged

#### Scenario: Invalid evidence has no partial response
- **WHEN** persisted v2 evidence fails strict validation
- **THEN** the endpoint returns the standard error envelope and no partial Walk-forward detail
