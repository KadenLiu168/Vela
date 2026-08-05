## Context

Every successful Walk-forward window already owns one persisted successful `BacktestRun`, and every such run owns a date-ordered `BacktestEquityCurve` normalized to `1.000000` at its first test session. `WalkForwardRunWindow` preserves chronological ordinal and exact test bounds, while the parent `wf_provenance_v1` manifest preserves the official-session axis used to construct those windows. The current detail query eagerly loads OOS runs and benchmarks but not their curves; the API and Web intentionally expose no continuous curve because the existing specification forbids joining independent windows.

The requested capital path changes that presentation contract but does not make the selected parameter sequence a continuously held strategy. Each OOS run initializes its own portfolio state at the first session, and the first point is a zero-return initialization artifact. The design therefore compounds only returns already present inside each persisted curve and makes every later window boundary an explicit reset. Current code, tests, and persisted rows remain the source of truth; `vela.db` is not used for validation or migration.

## Goals / Non-Goals

**Goals:**

- Produce one deterministic, auditable curve whose ending value equals chronological compounding of every selected OOS segment's realized net-value factor.
- Reject missing or malformed evidence instead of guessing seam behavior, while distinguishing valid non-contiguous window configurations from corruption.
- Add the curve and cumulative result to the existing read-only Walk-forward detail API and Web page.
- Preserve source-window ownership and communicate reset semantics clearly enough that the chart cannot reasonably be mistaken for uninterrupted holdings.
- Reuse existing persisted curves and chart primitives without a schema migration or data duplication.

**Non-Goals:**

- No holdings carryover, boundary rebalance simulation, seam transaction cost, gap return, benchmark stitching, or claim of directly tradable continuity.
- No new cross-window Sharpe, volatility, drawdown, drawdown-duration, Calmar, Tracking Error, Information Ratio, score, or pass/fail result.
- No CLI report curve, execution change, persistence version change, backfill, new endpoint, dependency, or Dashboard content.

## Decisions

### Derive from persisted curves at read time

Add a small pure core helper for stitched-curve validation and arithmetic. The Walk-forward detail query eagerly loads each selected OOS run's ordered `equity_curve` collection in addition to benchmarks, validates the persisted parent/child ownership as today, and derives `stitched_oos` only for the requested detail. The list endpoint remains unchanged and never loads curve rows.

This keeps the source OOS curves authoritative, avoids storing data that can be reproduced exactly, requires no Alembic revision, and makes existing successful histories immediately readable. Materializing a new parent curve was rejected because it duplicates evidence, introduces migration/backfill and consistency rules, and can drift from its source rows. Deriving in React was rejected because financial validation and Decimal arithmetic belong in the typed backend and would create two contract implementations.

### Require a complete official-session chain and distinguish non-contiguity

Resolve every persisted test bound in the parent's ordered `official_sessions` manifest. The first window may start anywhere in that axis; every later `test_start` must be the immediately following official session after the prior `test_end` for a stitched path to be available. A gap or overlap is a valid outcome of the currently permitted `step_years`/`test_years` configuration, so it returns `unavailable_non_contiguous_windows` with no curve or cumulative values while preserving the full independent-window detail.

Only when the window chain is contiguous, additionally require every source OOS curve to be non-empty; have strictly increasing unique point dates and positive net values; and have first/last point dates equal to its persisted `test_start`/`test_end`. A missing manifest bound or malformed eligible curve raises `PersistedDataContractError`, which the existing API error boundary maps to the standard unexpected response without partial data.

Treating gaps as flat capital was rejected because it implies unrecorded cash exposure. Serializing overlapping windows was rejected because two selected parameter states would own the same session and the date axis would cease to be monotonic. Treating either valid configuration as corruption was also rejected because it would break existing detail reads. Inferring adjacency from calendar dates was rejected because weekends, holidays, suspensions, and the repository's fail-fast trading-calendar contract make the persisted official-session axis authoritative.

### Compound source factors without inventing a seam return

Maintain an unrounded Decimal capital factor beginning at one. For each source segment, capture its positive first local value `L0`; transform every point `Li` to `capital_at_start × Li / L0`; and set the next segment's entering capital to the unrounded transformed final point. Quantize only exposed point values, ending value, and total return to six decimal places using the repository's existing Decimal convention. The final total return is `unrounded_ending / 1 - 1`, so it equals the product of the source segment terminal factors minus one rather than a sum of window returns.

Retain the first point of later windows. It has the previous segment's ending capital, `is_window_start = true`, and its own `window_ordinal`; it is an explicit zero-return/reset marker, not a duplicated date. Remaining points are marked false. Skipping this point was rejected because it would hide where parameter/portfolio state resets. Creating a synthetic point between windows was rejected because no authoritative price, holding, turnover, or cost observation exists there.

### Add one exact detail response object

Extend `WalkForwardDetailResponse` with required `stitched_oos`:

- `status`: `available` or `unavailable_non_contiguous_windows`.
- `initial_net_value`: Decimal string `1.000000` when available, otherwise null.
- `ending_net_value` and `total_return`: six-place Decimal strings when available, otherwise null.
- `points`: ordered objects containing `trade_date`, six-place `net_value`, `window_ordinal`, and `is_window_start` when available, otherwise empty.

The API router serializes the core result; it does not recalculate it. The result object is required so unavailability is explicit rather than silently absent. Legitimate non-contiguity preserves the complete detail with a typed unavailable status; corrupt evidence for a contiguous, eligible curve still fails closed. A bare nullable field was rejected because it cannot distinguish a valid unsupported window shape from missing/corrupt data.

### Reuse the existing chart presentation with explicit semantics

Add a dedicated stitched OOS section near the aggregate evidence and before the per-window table. For available results, reuse the existing equity-curve chart/normalization primitives where their contract accepts typed date/value points; otherwise extract only the smallest shared chart adapter needed by Backtest Detail and Walk-forward Detail. Display ending net value and cumulative total return from the API, not browser arithmetic. Mark or list each window-start date and ordinal in accessible content, add a programmatic chart label, and place a concise disclosure beside the chart explaining per-window reset and omitted seam effects. For non-contiguous results, render a concise unavailable explanation and keep all other evidence visible.

The page retains existing responsive behavior at 1440x1000 and 390x844. No separate visualization framework or generalized multi-series chart is introduced.

### Verify arithmetic, integrity, transport, and presentation independently

Core tests use hand-derived segments, including `1.0 → 1.1` followed by `1.0 → 0.9`, to prove multiplicative `0.99` ending capital and `-0.01` total return; cover more than two windows and precision; independently reject empty/non-positive/duplicate/non-increasing/mismatched-bound curves; and prove gaps/overlap return typed unavailability without invalidating the parent evidence. Query tests verify eager-loaded eligible histories derive without N+1 access assumptions and corrupt eligible histories fail closed. API tests lock the exact OpenAPI/JSON shape, both statuses, Decimal strings, reset markers, strategy scoping, and no partial error response. Web tests verify API values are displayed unchanged, reset semantics and unavailable explanation are visible, the chart is labeled, and both required viewports avoid page overflow.

After focused checks, the implementation must run the complete Python and Web gates because both stacks change. Database integration uses test-owned temporary SQLite files only.

## Risks / Trade-offs

- [The stitched line may be read as a live tradable portfolio] → label it as compounded OOS segments, expose every reset boundary, and explicitly disclose omitted seam holdings/turnover/cost.
- [Historical curve corruption becomes visible as a 500 for contiguous eligible detail] → fail closed with focused diagnostics and no partial response; valid gaps/overlaps use typed unavailability instead.
- [Long histories increase detail payload and query size] → load curves only for one detail request; keep list payloads unchanged and avoid duplicate persisted data.
- [Intermediate rounding can distort compounding] → retain unrounded Decimal capital through all segments and quantize only public values.
- [A chart refactor could expand Web scope] → reuse current primitives or extract only the narrow adapter required by the two detail pages.

## Migration Plan

1. Add the pure derivation and integrity tests, then integrate eager loading and query-level validation against temporary SQLite histories.
2. Extend API schemas/router and lock response/OpenAPI/error contracts.
3. Add the Walk-forward detail section and responsive/accessibility tests.
4. Run focused checks, complete Python gate, complete Web gate, strict target/global OpenSpec validation, and independent requirement-to-code-to-test review.

There is no database or persisted-document migration. Rollback removes the derived response field and Web section; authoritative OOS curves and Walk-forward records remain unchanged.

## Open Questions

None. The curve is strategy-only, read-time derived for adjacent official-session windows, explicitly unavailable without hiding evidence for valid gaps/overlaps, and preserves per-window reset semantics.
