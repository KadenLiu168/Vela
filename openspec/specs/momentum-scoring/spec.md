# momentum-scoring Specification

## Purpose
Define how Vela calculates reproducible weighted momentum scores from configured strategy windows and weights.
## Requirements
### Requirement: Weighted momentum score calculation
The system SHALL calculate a weighted momentum score for one ETF using the configured short and long momentum windows and score weights.

#### Scenario: Calculate weighted score from complete configured windows
- **WHEN** backend code calculates a momentum score for an ETF and `as_of_date` with enough `MarketPrice` history for the configured short and long windows
- **THEN** the system returns the short-window return
- **AND** the system returns the long-window return
- **AND** the system returns a score equal to `short_return * score_weights.short + long_return * score_weights.long`

#### Scenario: Calculate weighted scores for multiple configured combinations
- **WHEN** backend code calculates momentum scores for multiple valid short/long momentum window pairs and score weight pairs
- **THEN** each calculation returns component returns from the corresponding configured trading-row windows
- **AND** each calculation returns a score equal to `short_return * score_weights.short + long_return * score_weights.long`
- **AND** repeating the calculation with identical stored prices and strategy configuration returns the same component returns and weighted score

#### Scenario: Use configured windows instead of fixed market return windows
- **WHEN** backend code calculates a momentum score with configured short and long momentum windows
- **THEN** each component return uses the corresponding configured trading-row window
- **AND** the calculation does not require the fixed 20 / 60 / 120 market return windows

#### Scenario: Reproduce score for identical inputs
- **WHEN** backend code calculates a momentum score multiple times with the same ETF, `as_of_date`, stored prices, and strategy configuration
- **THEN** each calculation returns the same component returns and weighted score

#### Scenario: Missing component return produces no score
- **WHEN** backend code calculates a momentum score and either configured momentum window has insufficient price history
- **THEN** the missing component return is null
- **AND** the weighted score is null

#### Scenario: Missing current price produces no score
- **WHEN** backend code calculates a momentum score and no `MarketPrice` exists for the requested ETF on the requested `as_of_date`
- **THEN** the short-window return is null
- **AND** the long-window return is null
- **AND** the weighted score is null

#### Scenario: Isolate ETF histories
- **WHEN** backend code calculates a momentum score and market prices exist for multiple ETFs
- **THEN** the calculation only uses `MarketPrice` rows for the requested ETF

### Requirement: ETF momentum score ranking
The system SHALL rank ETF candidates by calculated weighted momentum scores for Top N selection.

#### Scenario: Rank complete scores descending
- **WHEN** backend code ranks ETF momentum scores with non-null weighted scores
- **THEN** the ranked results are ordered by weighted score from highest to lowest
- **AND** each ranked result includes the ETF id, as-of date, weighted score, and rank

#### Scenario: Break equal-score ties by ETF id
- **WHEN** backend code ranks multiple ETF momentum scores with the same non-null weighted score
- **THEN** tied ETFs are ordered by ETF id ascending

#### Scenario: Exclude missing scores from ranking
- **WHEN** backend code ranks ETF momentum scores and one or more scores are null
- **THEN** ETFs with null scores are excluded from ranked results

#### Scenario: Assign continuous ranks after filtering
- **WHEN** backend code ranks ETF momentum scores after excluding null scores
- **THEN** ranks are assigned as continuous 1-based integers in sorted order

#### Scenario: Support Top N selection
- **WHEN** backend code takes the first configured Top N ranked results
- **THEN** the selected ETFs are the highest-ranked eligible ETFs

### Requirement: Top N ETF selection
The system SHALL select the configured Top N ETFs from ranked momentum results and return selection entries containing ETF id, rank, score, and target weight.

#### Scenario: Select configured Top N ranked ETFs
- **WHEN** backend code selects Top N ETFs from ranked momentum results using strategy configuration
- **THEN** the selected results include only the highest-ranked ETFs up to `selection.top_n`
- **AND** each selected result includes the ETF id, rank, score, and target weight

#### Scenario: Assign equal target weights to selected ETFs
- **WHEN** backend code selects one or more Top N ETFs
- **THEN** each selected result has a target weight equal to one divided by the number of selected ETFs

#### Scenario: Return all available ETFs when Top N is insufficient
- **WHEN** backend code selects Top N ETFs and fewer ranked ETFs are available than `selection.top_n`
- **THEN** the selected results include all available ranked ETFs
- **AND** target weights are assigned across the available selected ETFs

#### Scenario: Return an empty selection when no ranked ETFs exist
- **WHEN** backend code selects Top N ETFs from an empty ranked result set
- **THEN** the selected results are empty

### Requirement: Defensive asset fallback selection
The system SHALL apply the configured defensive asset when ranked ETF candidates cannot satisfy the configured Top N selection.

#### Scenario: Fallback when ranked ETFs are insufficient
- **WHEN** backend code applies defensive fallback selection and the number of ranked ETF candidates is less than `selection.top_n`
- **THEN** the selected result contains the configured `defense.asset` exchange and symbol
- **AND** the selected result has full target weight
- **AND** no risky ranked ETF candidates are selected

#### Scenario: Fallback when no ranked ETFs are available
- **WHEN** backend code applies defensive fallback selection and no ranked ETF candidates are available
- **THEN** the selected result contains the configured `defense.asset` exchange and symbol
- **AND** the selected result has full target weight
- **AND** no risky ranked ETF candidates are selected

#### Scenario: Do not fallback when Top N is satisfied
- **WHEN** backend code applies defensive fallback selection and the number of ranked ETF candidates is greater than or equal to `selection.top_n`
- **THEN** the selected results contain the configured Top N ranked ETF candidates
- **AND** the configured defensive asset is not selected

## Future Considerations

### Window re-anchoring to trading-day offsets (Alt C follow-up)

Momentum windows currently count by **stored `MarketPrice` rows** (position
indexing: `prices[-1-window]`), which equals "N trading days back" only when
the stored series is gap-free. With `trading_calendar` (see the
`trading-calendar` spec) and trading-day gap detection (see the
`trading-day-gap-detection` spec) now landed, gaps are visible and large
systematic gaps can hard-fail a backtest, but small tolerated gaps still shift
the window across the wrong time span.

Re-anchoring windows to true trading-day offsets would close the residual
accuracy gap. It is deliberately deferred because:

- The most dangerous failure mode — silent miscalculation with no
  traceability — is already closed by gap detection (gaps are now visible and
  large systematic gaps are strict-blocked before backtest execution).
- Alt C is an accuracy refinement for the "few gaps, chose to continue in
  `warn` mode" scenario, not a safety fix.
- It has the largest blast radius of any data-quality change: it changes
  window semantics across this spec, `market-data`, and `trend-filtering`;
  rewrites all window-related tests; and breaks comparability of historical
  `BacktestRun` results (identical inputs would yield different numbers after
  the semantic switch).

**Trigger for re-evaluation**: after running Phase 2 gap detection for a few
research cycles, if (a) `warn`-mode backtests are frequently continued and
their numbers are trusted, and (b) observed gaps are mostly small/systematic
rather than single-ETF halts, escalate Alt C into a change proposal. If in
practice gaps always lead to either data repair or `strict` refusal, Alt C is
likely not worth the blast radius and may remain deferred indefinitely.

Related specs: `market-data` (window return and moving-average row counting),
`trend-filtering` (moving-average window).
