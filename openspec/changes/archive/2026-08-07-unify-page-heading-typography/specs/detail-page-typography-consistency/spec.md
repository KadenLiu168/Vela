# detail-page-typography-consistency (delta)

## MODIFIED Requirements

### Requirement: 跨页面同层元素 typography 一致

Signal Detail、Backtest Detail、Dashboard 以及全部渲染 `page-heading h1` 的页面（Signal / Backtest / Walk-forward 列表页与详情页、ETF Detail）在共享结构（`page-heading`、`panel-primary`、`compact-list`、`holdings-section h3`、`holdings-table`）上的同层级元素 MUST 使用相同的字体族、字号、字重、行高、字距与 `text-transform` 修饰。差异仅允许出现在"各自独有的元素"上（如 Backtest 独有的 `.metric-card`、`.equity-curve-card`、`.parameter-summary`）。

#### Scenario: page-heading 标题与 eyebrow 视觉一致

- **WHEN** 用户分别打开 Dashboard、Signal List / Detail、Backtest List / Detail、Walk-forward List / Detail 与 ETF Detail 任意页面
- **THEN** 所有页面的 `page-heading h1` 必须使用相同的 `font-size`（`var(--text-heading-sm)`）、`line-height`、`letter-spacing` 与 `font-weight`
- **AND** 所有页面的 `page-heading p`（eyebrow）必须使用相同的 `font-size`、`text-transform` 与 `letter-spacing`

#### Scenario: panel-primary 视觉一致

- **WHEN** 用户分别打开 Signal Detail 页面、Backtest Detail 页面与 Dashboard 页面
- **THEN** 三个页面的 `.panel-primary`（"Signal #N" / "Backtest #N" / Strategy ID）必须使用相同的 `font-size`、`line-height`、`letter-spacing` 与 `font-weight`

#### Scenario: compact-list 字段 label 与 value 视觉一致

- **WHEN** 用户分别打开 Signal Detail 页面、Backtest Detail 页面与 Dashboard 页面
- **THEN** 三个页面的 `.compact-list dt`（字段 label）必须使用相同的 `font-size`、`line-height`、`text-transform` 与 `letter-spacing`
- **AND** 三个页面的 `.compact-list dd`（字段 value）必须使用相同的 `font-size`、`line-height` 与 `font-weight`

#### Scenario: holdings-section 章节标题视觉一致

- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个 detail 页面的 `.holdings-section h3` 必须使用相同的 `font-size`、`line-height`、`letter-spacing` 与 `font-weight`
- **AND** 该 requirement 仅适用于 detail 页面之间，不覆盖 Dashboard

#### Scenario: holdings-table 表头与单元格视觉一致

- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个 detail 页面的 `.holdings-table th` 必须使用相同的 `font-size`、`text-transform` 与 `letter-spacing`
- **AND** 两个 detail 页面的 `.holdings-table td` 必须使用相同的 `font-size` 与 `font-weight`
- **AND** 该 requirement 仅适用于 detail 页面之间，不覆盖 Dashboard
