## ADDED Requirements

### Requirement: Backtest responses expose stored distribution-risk evidence
Successful backtest-run and detail responses SHALL expose nullable Historical VaR 95%, Historical CVaR 95%, Skewness, Excess Kurtosis, effective observation count, tail observation count, and derived `sufficient`/`insufficient_evidence` status for the strategy and each fixed benchmark. Decimal values SHALL be six-place strings, routers MUST NOT recompute metrics, and legacy null counts SHALL produce an explicit unavailable legacy status rather than an assumed zero sample.

#### Scenario: New response preserves stored values and positive-loss sign
- **WHEN** a newly calculated benchmark-enabled run is serialized
- **THEN** strategy and both benchmark objects return exact stored metrics/counts and derived statuses
- **AND** returned VaR/CVaR values satisfy the positive-loss invariant

#### Scenario: Legacy response does not fabricate evidence
- **WHEN** a legacy run or benchmark has null distribution fields and counts
- **THEN** new metric fields remain null with an explicit legacy-unavailable status

### Requirement: Walk-forward Detail exposes validated v3 distribution evidence
Walk-forward Detail SHALL serialize validated `wf_evidence_v3` per-window and aggregate distribution groups with named owners, metric-local counts, and statuses. Valid v1/v2 detail SHALL remain readable according to its version, and OpenAPI SHALL distinguish supported shapes without browser inference.

#### Scenario: V3 response matches validated history
- **WHEN** a client requests a valid v3 Walk-forward history
- **THEN** every distribution value, count, null, status, and owner matches the validated evidence document

#### Scenario: Invalid v3 returns no partial detail
- **WHEN** persisted v3 evidence violates its strict contract
- **THEN** the endpoint returns the standard error envelope and no partial Walk-forward response
