## MODIFIED Requirements

### Requirement: API returns one typed Walk-forward evaluation detail
The API SHALL expose `GET /api/walk-forwards/{run_id}` with typed ISO dates/timestamps, persisted decimal strings, provenance/evidence versions and checksums, manifest, aggregate evidence, ordered windows, OOS links, fixed benchmark data, and a non-null `stitched_oos` result derived from authoritative persisted evidence. `stitched_oos.status` SHALL be `available` when the windows are contiguous or `unavailable_non_contiguous_windows` when otherwise valid windows have a gap or overlap. An available result SHALL contain Decimal strings `initial_net_value`, `ending_net_value`, and `total_return`, plus chronological `points`; every point SHALL contain ISO `trade_date`, six-place Decimal-string `net_value`, integer `window_ordinal`, and boolean `is_window_start`. An unavailable result SHALL contain null cumulative values and an empty points list while the rest of the detail remains complete. Unknown and other-strategy ids SHALL use the standard 404 contract. Unsupported or corrupt persisted documents, OOS ownership, eligible source curves, or official-session manifests SHALL use the standard unexpected-error contract without partial detail data.

#### Scenario: Detail preserves ordered ownership
- **WHEN** a current-strategy persisted evaluation with valid adjacent OOS windows is requested
- **THEN** each window exposes its selected OOS run and both fixed benchmarks in chronological order
- **AND** `stitched_oos.status` is `available` and exposes the deterministic compounded points and cumulative result in the same window order

#### Scenario: Reset boundary is machine-readable
- **WHEN** a Walk-forward detail contains more than one stitched OOS segment
- **THEN** the first point for each segment identifies its owning `window_ordinal` and has `is_window_start = true`
- **AND** every later point in that segment has `is_window_start = false`

#### Scenario: Invalid stitched evidence returns no partial detail
- **WHEN** contiguous persisted windows are eligible for stitching but their OOS curves or official-session manifest is corrupt
- **THEN** the API returns the standard unexpected-error envelope
- **AND** it does not return windows, a partial curve, or a cumulative result

#### Scenario: Non-contiguous windows preserve complete detail
- **WHEN** a valid persisted evaluation has an official-session gap or overlap between ordered OOS windows
- **THEN** the API returns the complete Walk-forward detail with `stitched_oos.status = unavailable_non_contiguous_windows`
- **AND** cumulative values are null and points are empty
