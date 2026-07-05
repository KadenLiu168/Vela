## ADDED Requirements

### Requirement: Detail 页面同层元素 typography 一致
Signal Detail 与 Backtest Detail 两个 detail 页面在共享结构（`page-heading`、`panel-primary`、`compact-list`、`holdings-section h3`、`holdings-table`）上的同层级元素 MUST 使用相同的字体族、字号、字重、行高、字距与 `text-transform` 修饰。差异仅允许出现在"各自独有的元素"上（如 Backtest 独有的 `.metric-card`、`.equity-curve-card`、`.parameter-summary`）。

#### Scenario: page-heading 标题与 eyebrow 视觉一致
- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个页面的 `page-heading h2` 必须使用相同的 `font-size`、`line-height`、`letter-spacing` 与 `font-weight`
- **AND** 两个页面的 `page-heading p`（eyebrow）必须使用相同的 `font-size`、`text-transform` 与 `letter-spacing`

#### Scenario: panel-primary 视觉一致
- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个页面的 `.panel-primary`（"Signal #N" / "Backtest #N" 标题）必须使用相同的 `font-size`、`line-height`、`letter-spacing` 与 `font-weight`

#### Scenario: compact-list 字段 label 与 value 视觉一致
- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个页面的 `.compact-list dt`（字段 label）必须使用相同的 `font-size`、`line-height`、`text-transform` 与 `letter-spacing`
- **AND** 两个页面的 `.compact-list dd`（字段 value）必须使用相同的 `font-size`、`line-height` 与 `font-weight`

#### Scenario: holdings-section 章节标题视觉一致
- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个页面的 `.holdings-section h3` 必须使用相同的 `font-size`、`line-height`、`letter-spacing` 与 `font-weight`

#### Scenario: holdings-table 表头与单元格视觉一致
- **WHEN** 用户分别打开 Signal Detail 页面与 Backtest Detail 页面
- **THEN** 两个页面的 `.holdings-table th` 必须使用相同的 `font-size`、`text-transform` 与 `letter-spacing`
- **AND** 两个页面的 `.holdings-table td` 必须使用相同的 `font-size` 与 `font-weight`

### Requirement: compact-list 字段 label 与 value baseline 对齐
两个 detail 页面的 `.compact-list dt`（label）与 `.compact-list dd`（value）在同一 grid 行内 MUST 保持 baseline 视觉对齐——label 文字与 value 文字的基线在水平方向上重合，行内不出现"label 偏上、value 偏下"或反之的视觉错位。

#### Scenario: 同行 dt 与 dd baseline 对齐
- **WHEN** 任意 detail 页面渲染出 compact-list 中的一行（一个 dt + 一个 dd）
- **THEN** 该行内 dt 文字与 dd 文字的视觉 baseline 必须处于同一水平线
- **AND** dt 字号与 dd 字号差不得超过 0（即二者字号相同）

#### Scenario: 不依赖 uppercase 与否的 baseline 稳定性
- **WHEN** compact-list 中 dt 文字使用 `text-transform: uppercase`
- **THEN** 即使大小写转换改变了字形视觉中心，dt 与 dd 的 baseline 仍必须保持对齐
- **AND** 同行 row 高度由 dt 与 dd 共享的 `line-height` 决定，而非字号差

### Requirement: detail 页面 typography 不向 Dashboard 页面泄漏
两个 detail 页面合并后的 `.detail-page .x` CSS 规则 MUST NOT 影响 `.dashboard-page` 作用域下任何元素的视觉表现。

#### Scenario: Dashboard 页面 typography 保持原样
- **WHEN** 合并后的 `.detail-page .dashboard-panel`、`.detail-page .panel-primary`、`.detail-page .compact-list`、`.detail-page .holdings-section h3` 规则生效
- **THEN** Dashboard 页面（`.dashboard-page` 作用域）所有元素的 `font-size`、`line-height`、`letter-spacing`、`text-transform` 必须与合并前完全一致

#### Scenario: compact-list 在 dashboard 上下文中的视觉保持
- **WHEN** Dashboard 页面渲染其 `.compact-list`
- **THEN** 该 `.compact-list` 的 `dt` 与 `dd` 视觉必须与合并前完全一致
- **AND** `.dashboard-page .compact-list dt` 规则（在 643 行）必须保持继续生效
