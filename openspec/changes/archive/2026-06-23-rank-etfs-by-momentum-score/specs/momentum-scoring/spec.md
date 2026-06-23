## ADDED Requirements

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
