# web-route-code-splitting Specification Delta

## MODIFIED Requirements

### Requirement: Production bundle structure and budget bands are verifiable
The web frontend SHALL provide a repeatable production-build check that derives static and dynamic chunk relationships from a fresh Vite manifest, reports raw and gzip JavaScript sizes, attributes required runtime separately from eager application code and non-initial lazy-route JavaScript, reports every lazy route entry and asynchronous shared chunk separately, evaluates every configured budget band in one run, and returns a non-zero result when any identity, budget, or graph-ownership requirement fails.

#### Scenario: Bundle evidence comes from the reviewed dependency and source state
- **WHEN** production bundle acceptance is recorded
- **THEN** dependencies MUST be installed from the reviewed npm lockfile before a fresh production build
- **AND** the evidence MUST identify the Node, npm, Vite, and lockfile state that produced the manifest
- **AND** an older `dist/` tree MUST NOT be accepted as evidence for changed source, dependencies, or build tooling

#### Scenario: Reviewed build identity is pinned to the evidence
- **WHEN** production bundle acceptance is recorded
- **THEN** the report MUST identify the Node, npm, Vite, and npm lockfile identity that produced the manifest
- **AND** the identity MUST match the reviewed build identity for this Change
- **AND** a dependency or toolchain identity change MUST be reported as a baseline violation rather than silently accepted

#### Scenario: Required runtime and eager application bands are reported separately
- **WHEN** the production bundle check evaluates the Dashboard initial static JavaScript graph
- **THEN** it MUST report the isolated required React 19 + React Router runtime baseline separately from eager application code
- **AND** the required runtime baseline MUST be `229,187` raw bytes and `73,544` gzip bytes for the reviewed identity
- **AND** eager application code MUST be no greater than `53,000` raw bytes and `15,000` gzip bytes

#### Scenario: Dashboard initial graph stays within the revised budget
- **WHEN** the production bundle check evaluates the Dashboard initial static JavaScript graph
- **THEN** the summed raw JavaScript size MUST be no greater than 283,000 bytes
- **AND** the summed gzip JavaScript size MUST be no greater than 89,000 bytes

#### Scenario: Lazy route graph stays within the revised allocation
- **WHEN** the production bundle check evaluates all emitted JavaScript that is not in the Dashboard initial static graph
- **THEN** the summed raw JavaScript size MUST be no greater than 70,000 bytes
- **AND** the report MUST include asynchronous shared helper chunks in this allocation

#### Scenario: Total JavaScript avoids material growth
- **WHEN** the production bundle check evaluates every emitted JavaScript chunk
- **THEN** the summed raw JavaScript size MUST be no greater than 349,000 bytes
- **AND** the report MUST list each asynchronous route entry separately from the initial static graph

#### Scenario: Eager-band revision is evidence-backed
- **WHEN** the eager application, initial, or total band is revised
- **THEN** the change that revised it MUST record, in a bundle-evidence document, the pre-change and post-change measurement for every revised band, the build identity that produced the post-change measurement, and the reason the added eager code is required on the first screen
- **AND** a revised band MUST NOT be set below the recorded measurement
- **AND** the revision MUST be accompanied by the same change's specification delta rather than applied to the checker alone

#### Scenario: Lazy route contributors are attributable
- **WHEN** production bundle remediation evidence is recorded
- **THEN** the report MUST identify the raw byte size of each Signal list/detail, Backtest list/detail, ETF detail, and Walk-forward list/detail entry chunk
- **AND** it MUST list non-initial shared JavaScript chunks separately so shared bytes are counted exactly once in the lazy aggregate
- **AND** the sum of all reported non-initial entry and shared chunks MUST equal the reported lazy-route raw total

#### Scenario: Every declared lazy route is verified
- **WHEN** the production bundle check evaluates the Vite manifest and built Dashboard HTML
- **THEN** it MUST locate separate dynamic entries for Signal list/detail, Backtest list/detail, ETF detail, Walk-forward list/detail
- **AND** none of those route entries may belong to the Dashboard initial static graph or appear in Dashboard module-preload markup

#### Scenario: One run reports every bundle violation
- **WHEN** identity, required-runtime, eager-application, lazy-route, initial, total JavaScript, or lazy-route ownership exceeds its contract
- **THEN** the checker MUST report every violated condition from that build rather than stopping after the first failure
- **AND** the checker MUST exit non-zero without changing, bypassing, or silently rebaselining the configured thresholds

#### Scenario: Font and JavaScript results remain separate
- **WHEN** performance results for this change are recorded
- **THEN** JavaScript graph sizes MUST be reported independently from font transfer sizes
- **AND** font-subsetting savings MUST NOT be attributed to route code splitting
