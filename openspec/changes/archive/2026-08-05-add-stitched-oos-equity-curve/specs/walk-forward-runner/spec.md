## MODIFIED Requirements

### Requirement: OOS windows remain isolated evidence
Each selected OOS backtest SHALL remain the authoritative evidence owner for its own evaluation interval. When the ordered OOS windows are non-overlapping and their test intervals are adjacent on the persisted `wf_provenance_v1` official-session axis, the system SHALL derive one stitched OOS capital path by scaling each complete source equity curve into the capital ending the previous segment. For a segment with positive initial local net value `L0`, local point value `Li`, and unrounded capital `C` entering the segment, its stitched point SHALL equal `C × Li / L0`; `C` for the next segment SHALL equal the current segment's unrounded final stitched value. The first stitched value SHALL be `1.000000`, exposed point values and the ending value SHALL use six decimal places, and cumulative total return SHALL equal the unrounded ending value divided by the initial value minus one, quantized to six decimal places. When otherwise valid ordered windows have a gap or overlap on that axis, derivation SHALL return the explicit `unavailable_non_contiguous_windows` status with no curve or cumulative values; non-contiguity alone MUST NOT invalidate the persisted Walk-forward detail.

The first point of every later segment SHALL remain in the stitched series at the preceding segment's ending capital and SHALL be identified as that window's reset boundary. It MUST NOT create a return observation, carry holdings across windows, or synthesize transaction cost, turnover, price movement, or exposure between the two source curves. The stitched path represents continuous compounding of the persisted OOS segment returns under the existing per-window reset semantics; it MUST NOT be represented as one continuously held or directly tradable portfolio and MUST NOT be used to derive unrequested cross-window Sharpe, volatility, Calmar, drawdown-duration, or benchmark-relative metrics.

#### Scenario: Adjacent windows compound their realized factors
- **WHEN** two adjacent OOS curves run from `1.000000` to `1.100000` and from `1.000000` to `0.900000`
- **THEN** the stitched curve starts at `1.000000`, enters the second window at `1.100000`, and ends at `0.990000`
- **AND** its cumulative total return is `-0.010000`

#### Scenario: Window seam remains an explicit reset
- **WHEN** the next adjacent OOS window begins after the preceding window's final official session
- **THEN** its first stitched point equals the preceding window's ending capital and is marked with the next window ordinal as a window start
- **AND** no return, turnover, transaction cost, or holdings continuity is inferred at that boundary

#### Scenario: Valid non-contiguous windows remain readable
- **WHEN** otherwise valid ordered OOS windows have an official-session gap or overlap
- **THEN** stitched derivation reports `unavailable_non_contiguous_windows` with no points or cumulative values
- **AND** the Walk-forward's independent window evidence remains valid and readable

#### Scenario: Invalid source evidence fails closed
- **WHEN** contiguous windows are eligible for stitching but a source OOS curve is empty, has a non-positive net value, contains duplicate or non-increasing dates, does not cover its persisted test bounds, or its bounds cannot be resolved on the persisted official-session axis
- **THEN** stitched-curve derivation raises the persisted-data contract error
- **AND** no partial stitched path or cumulative return is returned

### Requirement: Selected OOS evidence includes expanded risk metrics
After `strengthen-walk-forward-evaluation-contract`, each selected OOS window SHALL retain strategy Sortino, Calmar and longest drawdown duration and each fixed benchmark comparison SHALL retain Tracking Error and Information Ratio. The report SHALL aggregate each strategy metric and each benchmark-relative metric separately using the existing metric-local valid-count and evidence-status contract. A stitched OOS capital path MAY be derived under the `OOS windows remain isolated evidence` requirement, but it MUST NOT change any per-window or aggregate risk metric and MUST NOT introduce cross-window Calmar or drawdown-duration calculations.

#### Scenario: OOS windows aggregate downside metrics
- **WHEN** three selected OOS runs contain valid Sortino and Calmar values
- **THEN** the evidence report includes their descriptive summaries and sufficient valid counts

#### Scenario: Benchmark active metrics remain keyed
- **WHEN** selected OOS runs contain TE/IR for both fixed benchmarks
- **THEN** the report aggregates TE/IR separately for `equal_weight_monthly` and `csi_300_buy_hold`

#### Scenario: Stitched path does not redefine risk evidence
- **WHEN** a stitched OOS capital path is derived across adjacent windows
- **THEN** every existing strategy and benchmark evidence summary remains calculated from its original window-local values
- **AND** no cross-window Calmar or drawdown-duration metric is calculated
