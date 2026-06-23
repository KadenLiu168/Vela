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

