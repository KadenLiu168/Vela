## ADDED Requirements

### Requirement: Walk-forward API exposes versioned input provenance
Walk-forward Detail SHALL expose validated input provenance as an explicit typed union discriminated by `wf_provenance_v1` or `wf_provenance_v2`. The v1 response SHALL retain its existing manifest shape. The v2 response SHALL include resolution policy version, ETF fund-inception/listing metadata, reconciled raw and derived counts/bounds, and bounded authoritative non-trading status/source evidence. OpenAPI SHALL distinguish the two shapes without requiring client inference. Unsupported, corrupt, or unreconciled provenance MUST return the standard unexpected-error envelope without partial detail.

#### Scenario: V2 detail exposes status-aware provenance
- **WHEN** a client requests a valid v2 Walk-forward run
- **THEN** the response preserves exact listing, policy, raw/derived count, carried-value, status, reason, source, and ratio fields from validated history
- **AND** OpenAPI identifies the response as the v2 branch

#### Scenario: V1 detail remains compatible
- **WHEN** a client requests a valid legacy v1 Walk-forward run
- **THEN** the response retains the existing v1 manifest and does not fabricate listing or status evidence

#### Scenario: Corrupt v2 has no partial response
- **WHEN** v2 provenance fails reconciliation or checksum validation
- **THEN** the endpoint returns the standard unexpected-error envelope
- **AND** returns no partial run, window, or provenance data
