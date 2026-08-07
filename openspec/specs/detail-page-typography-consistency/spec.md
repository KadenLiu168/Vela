# detail-page-typography-consistency Specification

## Purpose
Ensures typographic consistency for shared structural elements (`page-heading`, `panel-primary`, `compact-list`, `holdings-section`, `holdings-table`) across the Signal Detail, Backtest Detail, and Dashboard pages.
## Requirements
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

### Requirement: compact-list 字段 label 与 value baseline 对齐

Signal Detail、Backtest Detail 与 Dashboard 三个页面的 `.compact-list dt`（label）与 `.compact-list dd`（value）MUST 在同一 grid 行内保持 baseline 视觉对齐——label 文字与 value 文字的基线在水平方向上重合，行内不出现"label 偏上、value 偏下"或反之的视觉错位。

#### Scenario: 跨页面同行 dt 与 dd baseline 对齐
- **WHEN** 任意上述页面渲染出 compact-list 中的一行（一个 dt + 一个 dd）
- **THEN** 该行内 dt 文字与 dd 文字的视觉 baseline 必须处于同一水平线
- **AND** 行高度由 dt 与 dd 共享的 `line-height` token 决定（即 dt 与 dd 都引用同一个 `--leading-*` token）

#### Scenario: 不依赖 uppercase 与否的 baseline 稳定性
- **WHEN** compact-list 中 dt 文字使用 `text-transform: uppercase`
- **THEN** 即使大小写转换改变了字形视觉中心，dt 与 dd 的 baseline 仍必须保持对齐
- **AND** 同行 row 高度由 dt 与 dd 共享的 `--leading-*` 决定

### Requirement: Dashboard 与 Detail 共用 compact-list / panel-primary 基础规则

Dashboard 页面 (`.dashboard-page`) 与 Detail 页面 (`.detail-page`) 的 `.compact-list`、`.panel-primary`、`.metric span` 等卡片元素 MUST 直接消费 `card-type-scale` 的 ladder token，而不是依赖任何作用域覆盖层（descendant selector override）来维持视觉差异。

#### Scenario: 共享卡片元素跨页面 token 解析一致
- **WHEN** Dashboard 与 Detail 任意页面渲染
      `.compact-list dt`、`.compact-list dd`、
      `.panel-primary` 或 `.metric span`
- **THEN** 这些元素的 `font-size` / `line-height` /
      `letter-spacing` / `font-weight` 必须解析到完全相同的
      CSS 自定义属性值集合（由 `card-type-scale` 提供）
- **AND** 上述解析一致性必须由基础规则（无 `.dashboard-page`
      或 `.detail-page` 前缀）达成，而非由覆盖层修饰

#### Scenario: 共享卡片元素无 descendant 覆盖
- **WHEN** `apps/web/src/styles.css` 被搜索是否存在形如
      `.dashboard-page .compact-list *` 或
      `.detail-page .compact-list *` 的覆盖选择器
- **THEN** 该类选择器 MUST NOT 出现在共享卡片元素
      （`.compact-list dt/dd`、`.panel-primary`、
      `.metric span/strong`）的字号或字重声明上
- **AND** 视觉差异仅允许存在于 Dashboard 或 Detail 各自独有
      的元素（Dashboard 独有 `.etf-row`、`.metric-row`；
      Detail 独有 `.holdings-*`、`.equity-curve-card`、
      `.parameter-summary`）

