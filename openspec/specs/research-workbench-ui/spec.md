# research-workbench-ui Specification

## Purpose
Defines the Dashboard's decision-first information architecture: the five research layers it presents in order (current state, latest signal, strategy performance, OOS robustness, deep evidence), what each layer may assert about the artifacts it shows, and the boundary against fabricating currency, provenance, or verdicts.

## Requirements

### Requirement: Dashboard presents five decision layers in research order
The Dashboard SHALL render its loaded state as five sequential decision layers in this order: current state, latest signal, strategy performance, OOS robustness, and deep evidence. Each layer SHALL be a labeled region with its own accessible heading, and the five layers SHALL precede the reference and operations regions in document order. The page SHALL keep exactly one document-level `<h1>`.

#### Scenario: Layers render in decision order
- **WHEN** the Dashboard has loaded aggregate data
- **THEN** the current-state region renders first, followed by latest signal, strategy performance, OOS robustness, and deep evidence
- **AND** each region is introduced by its own heading
- **AND** the reference and operations regions follow all five decision layers

#### Scenario: Loading and error states do not render decision layers
- **WHEN** the Dashboard is loading, has failed, or has no aggregate data
- **THEN** no decision layer renders fabricated or placeholder metric values
- **AND** the existing loading feedback, error feedback, and first-run guidance remain visible

### Requirement: Current-state layer states freshness facts without fabricating currency
The first decision layer SHALL present, from aggregate date fields only, the market-data cutoff date, the latest signal date, the latest backtest date range, and the latest walk-forward run status. When the latest signal date precedes the market-data cutoff, or the latest backtest end date precedes the market-data cutoff, the layer SHALL state that the artifact lags the available data and SHALL show both dates. Lag duration SHALL be expressed in calendar days and SHALL NOT be described in trading-session units. The layer SHALL NOT compute any return, risk, or performance value, and SHALL NOT present a score, rating, or pass/fail verdict.

#### Scenario: Stale artifacts are named as lagging
- **WHEN** the latest successful signal date is earlier than the market-data latest trade date
- **THEN** the layer states that the signal lags the available market data
- **AND** it shows both the signal date and the market-data latest trade date
- **AND** any elapsed duration shown is labeled in calendar days

#### Scenario: Current artifacts are not described as lagging
- **WHEN** the latest successful signal date equals the market-data latest trade date
- **THEN** the layer does not describe the signal as lagging

#### Scenario: Missing artifacts are stated as missing
- **WHEN** the aggregate contains no latest signal, no recent backtest, or no walk-forward run
- **THEN** the layer states that the artifact does not exist yet
- **AND** it does not render a placeholder value in place of the missing artifact

#### Scenario: Freshness is display-level date comparison only
- **WHEN** the current-state layer renders at any time
- **THEN** every value it shows originates from an aggregate field
- **AND** no performance, risk, or return value is derived in the browser

### Requirement: Current-state layer offers the next research action
The current-state layer SHALL name at most one next research action and SHALL offer it as a control that moves focus to the pre-existing Dashboard control for that action rather than duplicating its trigger. The action SHALL be selected only from these conditions, in this priority order: no market data is stored, no successful signal exists, or the latest signal lags the market-data cutoff. A backtest whose range ends before the market-data cutoff SHALL be reported as a lagging fact but SHALL NOT on its own select an action, because an evaluation window is a deliberate research choice. The offered control SHALL NOT be the view's primary CTA.

#### Scenario: Action targets the missing artifact
- **WHEN** market data exists but no successful signal exists for the current strategy and config version
- **THEN** the layer offers exactly one next action that leads to signal generation
- **AND** it does not offer a market-data fetch as the same next action

#### Scenario: Action control is not the primary CTA
- **WHEN** the current-state layer renders its next-action control
- **THEN** the control does not use the shared primary fill
- **AND** the Dashboard's existing Bootstrap action remains the only prominent primary CTA, using the semantic interaction treatment

#### Scenario: A lagging backtest alone selects no action
- **WHEN** market data and a current latest signal exist and a backtest exists whose range ends before the market-data cutoff
- **THEN** the layer still reports that backtest range as lagging
- **AND** it offers no corrective action for it

#### Scenario: The no-action message claims only what the facts support
- **WHEN** the layer offers no corrective action while an artifact is displayed as lagging
- **THEN** the message SHALL NOT state that the lagging artifact is current
- **AND** it SHALL limit its claim to the artifacts it can support, or state only that no corrective action is needed

### Requirement: Latest-signal layer presents target holdings
The second decision layer SHALL render the latest successful signal's persisted target holdings from the aggregate, showing each position's exchange, symbol, name, target weight, rank, and score, plus the signal's date, result, fallback status, and source, and SHALL link to that signal's detail route. When the signal has no persisted positions, the layer SHALL state that no target holdings were stored.

#### Scenario: Holdings render from the aggregate
- **WHEN** the aggregate's latest signal carries positions
- **THEN** one row renders per position with exchange, symbol, name, target weight, rank, and score
- **AND** the layer links to `/signals/{signal_id}`

#### Scenario: Fallback positions are still shown
- **WHEN** a persisted position has a null rank and score
- **THEN** the row renders that position with the established unavailable-value treatment
- **AND** the layer states that fallback positions are present

#### Scenario: Empty holdings do not fabricate rows
- **WHEN** the aggregate's latest signal carries no positions
- **THEN** the layer states that no target holdings were stored for this signal

### Requirement: Latest-signal layer names the signal's provenance
Because the aggregate's latest signal may be a simulation artifact rather than a live instruction, the second decision layer SHALL state the signal's `source` using the same vocabulary as the Signals list. When the source is `backtest`, the layer SHALL additionally state that the holdings are that run's simulated positions rather than a current instruction, and SHALL link to the producing run's detail route when the aggregate carries its id. The layer SHALL NOT attach a simulation warning to a `manual` or `scheduled` source.

#### Scenario: A backtest-sourced signal is labelled as simulated
- **WHEN** the aggregate's latest signal has source `backtest` and a non-null `backtest_run_id`
- **THEN** the layer shows the `Backtest` source label
- **AND** it states that the holdings are simulated positions rather than a current instruction
- **AND** it links to `/backtests/{backtest_run_id}`

#### Scenario: A live signal carries no simulation warning
- **WHEN** the aggregate's latest signal has source `manual` or `scheduled`
- **THEN** the layer shows that source's label
- **AND** it does not state that the holdings are simulated

#### Scenario: Provenance vocabulary matches the Signals list
- **WHEN** the layer renders a source label
- **THEN** the label text is the one the Signals list uses for that source value
- **AND** both surfaces derive it from one shared label source

### Requirement: Strategy-performance layer contrasts the latest backtest with its primary benchmark
The third decision layer SHALL present the latest backtest's total return, calendar-time CAGR, Sharpe ratio, and max drawdown with their established convention labels, and SHALL present each value's difference against the run's primary benchmark when benchmark evidence exists. Benchmark-selected differences SHALL use the backend-published difference fields where the backend publishes them, and display-level subtraction of two published values elsewhere. The layer SHALL state the run's `config_version`, because the layer is a claim about the current strategy's performance and a run produced under an earlier version is only judgeable if that version is visible. The layer SHALL link to the run's detail route and SHALL NOT present a rank, score, or pass/fail verdict.

#### Scenario: Headline values carry their convention labels
- **WHEN** the third layer renders the latest backtest
- **THEN** `annualized_return` is labeled with its calendar-time CAGR convention
- **AND** `sharpe_ratio` is labeled with its daily-returns 252-session convention

#### Scenario: The run's config version is visible
- **WHEN** the third layer renders the latest backtest
- **THEN** it displays the run's `config_version`
- **AND** a run produced under a different version than the current one is therefore distinguishable from a current-version run

#### Scenario: Benchmark differences use published values
- **WHEN** the run's benchmark evidence contains a CSI 300 buy-and-hold entry
- **THEN** that entry is the primary benchmark for the layer
- **AND** the return differences use the backend-published difference fields

#### Scenario: No benchmark leaves differences unavailable
- **WHEN** the run has no benchmark evidence (a legacy run)
- **THEN** the layer renders the four strategy values without differences
- **AND** it does not fabricate a benchmark or a difference

#### Scenario: Missing backtest is stated, not synthesized
- **WHEN** the aggregate contains no recent backtest
- **THEN** the layer states that no local backtest run exists yet

### Requirement: OOS-robustness layer presents walk-forward evidence without scoring
The fourth decision layer SHALL present the latest walk-forward run for the current strategy: its status, test date range, and window count, and a link to that run's detail route. When a successful run carries persisted OOS evidence, the layer SHALL additionally present the cross-window median out-of-sample total return, median Sharpe, median max drawdown, positive-window rate, and primary-benchmark outperformance rate, plus the generalization gap statement and the evidence sufficiency statement — all from persisted evidence fields. When evidence is not available the layer SHALL state why in terms of the run's status, and SHALL NOT fabricate values. The layer SHALL NOT introduce a score, rating, ranking, threshold alert, or pass/fail conclusion.

#### Scenario: Successful run shows persisted OOS aggregates
- **WHEN** the latest walk-forward run has status `success` and carries persisted evidence
- **THEN** the layer shows the median OOS total return, median Sharpe, median max drawdown, positive-window rate with its fraction, and the primary benchmark's outperformance rate with its fraction
- **AND** every displayed value comes from the persisted evidence fields

#### Scenario: Evidence sufficiency is stated factually
- **WHEN** the layer renders the OOS evidence
- **THEN** it states the returned evidence status and the window count the status requires
- **AND** it does not convert the status into a pass/fail verdict

#### Scenario: Pre-terminal runs state their status
- **WHEN** the latest walk-forward run is `queued` or `running`
- **THEN** the layer states the run's status and that evidence is unavailable until it reaches a terminal state
- **AND** it does not render headline OOS values

#### Scenario: Failed runs state why evidence is unavailable
- **WHEN** the latest walk-forward run has status `failed`
- **THEN** the layer states that evidence is unavailable because the run failed
- **AND** it surfaces the API-provided error message when one is present

#### Scenario: No run is stated, not implied
- **WHEN** the aggregate contains no walk-forward run for the current strategy
- **THEN** the layer states that no walk-forward run exists yet
- **AND** it links to the Walk-forward list route as the place to start one

### Requirement: Deep-evidence layer indexes the existing research routes
The fifth decision layer SHALL provide labeled links to the existing Signals, Backtests, and Walk-forwards list routes and to the ETF market-data surface, without adding a new route or a new primary-navigation entry. Each link SHALL be reachable by keyboard and SHALL carry a name that states its destination.

#### Scenario: Evidence links target existing routes
- **WHEN** the fifth layer renders
- **THEN** it links to `/signals`, `/backtests`, and `/walk-forwards`
- **AND** it does not introduce a route that the application did not already serve

### Requirement: Reference and operations content is preserved and demoted
The Dashboard SHALL continue to render its market-data panel (including the `.etf-row-list` ETF rows), strategy-parameter panel, operations action list, backtest-run form, and data-fetch panel with their existing content and behavior, placed after the five decision layers. The existing panel labels SHALL match the `web-frontend-app` label requirement for the market and strategy panels. The Dashboard SHALL NOT add a new operation, a new API client function, or a new application state for the reference region.

#### Scenario: Operations behavior is unchanged
- **WHEN** the user triggers market-data fetch, signal generation, backtest run, or bootstrap from the demoted operations region
- **THEN** the existing pending, result, and error surfaces render as before

#### Scenario: ETF rows keep their contract
- **WHEN** the market-data panel renders a non-empty `etf_list`
- **THEN** it renders `.etf-row` elements inside `.etf-row-list` with symbol, name, and earliest trade date as before

### Requirement: Decision layers are responsive, keyboard accessible, and non-overflowing
Every decision layer SHALL use shared design tokens, SHALL remain keyboard operable with programmatically associated labels, and SHALL NOT cause page-level horizontal overflow at 1440x1000 or 390x844. A dense holdings table MAY use a labeled local scroll region.

#### Scenario: Narrow viewport keeps the decision path usable
- **WHEN** the Dashboard renders at 390x844
- **THEN** all five decision layers remain readable in order
- **AND** no page-level horizontal overflow occurs outside a labeled local table region
- **AND** every link and control remains reachable by keyboard

#### Scenario: Decision layers reuse the design system
- **WHEN** the decision layers render
- **THEN** no new button variant, no primary filled button beyond the view's primary CTA, and no non-token line-height is introduced
