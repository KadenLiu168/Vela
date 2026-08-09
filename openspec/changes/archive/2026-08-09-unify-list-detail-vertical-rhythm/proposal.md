## Why

Signals / Backtests / Walk-forwards 列表页的页面标题（`page-heading h1`，`margin-bottom: 0`）与下方内容（面板、Run 按钮）之间间距为 0px，而 Dashboard 页面使用 48px（`--space-xl`）的标题间距，观感拥挤且不一致。详情页（Walk-forward Detail 等）的章节标题 `<h2>` 在 `styles.css` 中没有任何样式规则，完全使用浏览器默认样式（`font-weight: bold`、`margin-block: 0.83em`），与设计体系的字重/间距不协调，标题与正文垂直节奏失衡。

## What Changes

- `styles.css` 新增 `.signal-list-page > :not(.page-heading), .backtest-list-page > :not(.page-heading) { margin-top: var(--space-xl); }`（48px）——Signals / Backtests 列表页标题与首个内容元素（dashboard-panel / empty-state / feedback-message）间距对齐 Dashboard。选择器用 `> :not(.page-heading)` 而非 `.dashboard-panel`：BacktestListPage 空 / loading / error 状态下首个内容元素是 `EmptyState` 或 `FeedbackMessage` 而非面板，`.dashboard-panel` 在这些状态不命中。选择器限定这两个列表页：Walk-forward 列表页首个内容元素是 `walk-forward-run-trigger` 而非面板（其标题间距由下一条 run-trigger `margin-top` 承担），宽选择器 `.list-page .dashboard-panel` 会命中该页自身的 `dashboard-panel` 并经 margin 合并吞掉 run-trigger 的 `margin-bottom: var(--spacing-16)`，故不采用。
- `styles.css` 为 `.walk-forward-run-trigger` 补充 `margin-top: var(--space-xl)`（保留现有 `margin-bottom: var(--spacing-16)`）——Walk-forwards 列表页标题与 Run 按钮间距对齐。
- `styles.css` 新增 `.holdings-section h2` 规则：`color: var(--color-paper)`、`font-family: var(--font-display)`、`font-size: var(--text-subheading)`、`font-weight: var(--font-weight-medium)`、`letter-spacing: var(--tracking-subheading)`、`line-height: var(--leading-subheading)`、`margin: 0 0 var(--spacing-16)`——详情页章节标题与下方正文间距受控（16px），规格与 `holdings-section h3` 体系一致。
- 全部为纯 CSS 改动，不涉及 JSX 或测试变更。

## Capabilities

### New Capabilities

（无新能力）

### Modified Capabilities

- `design-system`: 新增"标题与内容的垂直节奏"需求——页面标题与主内容之间 48px（`--space-xl`）、详情页章节标题与正文之间 16px（`--spacing-16`），间距通过 `--space-*` / `--spacing-*` token 表达。
- `detail-page-typography-consistency`: "holdings-section 章节标题视觉一致"从 `h3` 扩展到 `h2`——Walk-forward Detail 的 `h2` 与 Signal / Backtest Detail 的 `h3` 使用同一套章节标题规格。

## Impact

- `apps/web/src/styles.css`（新增三条规则）
- specs delta：`design-system`、`detail-page-typography-consistency`
- 无 API / 数据 / 依赖影响；无 JSX 与测试文件改动
