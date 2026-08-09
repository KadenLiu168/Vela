# Design — unify-list-detail-vertical-rhythm

## Context

`design-system` 的 spacing 需求要求布局间距通过 `--space-*` 语义阶梯表达（`--space-xl` = 48px）。当前页面级标题间距不一致：
- Dashboard：`.dashboard-grid` / `.first-run-guidance` 使用 `margin-top: calc(var(--section-gap) * 0.5)`（48px）；
- 列表页（Signals / Backtests / Walk-forwards）：`.page-heading h1` `margin-bottom: 0`，`.dashboard-panel` 无 margin-top，`.walk-forward-run-trigger` 仅有 `margin-bottom: var(--spacing-16)` —— 标题与内容间距实际为 0px。

详情页方面，`detail-page-typography-consistency` 只统一了 `holdings-section h3`（Signal / Backtest Detail 使用），Walk-forward Detail 的章节标题是 `<h2>`，在 `styles.css` 中无任何规则，回退到浏览器默认样式。

## Goals / Non-Goals

**Goals**
- 三个列表页标题与主内容间距统一为 48px（`--space-xl`），对齐 Dashboard 的页面级间距。
- 详情页章节标题（`h2`）补齐设计规格，与 `h3` 体系一致，标题与正文间距受控为 16px。
- 全部改动为 CSS，无 JSX / 测试变更，风险最小。

**Non-Goals**
- 不统一详情页 `h2`/`h3` 的标签层级混用（Walk-forward 用 h2、Backtest/Signal 用 h3）——涉及 JSX 与测试断言，属独立 change。
- 不调整 Dashboard 页间距（已是标准）。
- 不引入新 token（`--space-xl`、`--spacing-16`、`--text-subheading` 均已有）。

## Decisions

### D1: 列表页间距用 `var(--space-xl)` 而非 `calc(var(--section-gap) * 0.5)`
- **选择**：Signals / Backtests 列表页用 `.signal-list-page > :not(.page-heading), .backtest-list-page > :not(.page-heading) { margin-top: var(--space-xl) }`（48px，覆盖 page-heading 之后的首个内容元素——含 dashboard-panel、empty-state、feedback-message）；Walk-forward 列表页用 `.walk-forward-run-trigger { margin-top: var(--space-xl) }`（48px）。
- **理由**：`design-system` spacing 需求要求布局间距通过 `--space-*` 阶梯表达（"layout gaps use --space-* rather than ad-hoc spacing-N"）；`calc(var(--section-gap) * 0.5)` 是 Dashboard 的历史写法，新代码用 `--space-xl` 更符合契约，且解析值同为 48px，视觉一致。选择器用 `> :not(.page-heading)` 而非 `.dashboard-panel`：BacktestListPage 在空 / loading / error 状态下首个内容元素是 `EmptyState`（`.empty-state`）或 `FeedbackMessage`（`.feedback-message`）而非 `dashboard-panel`（`BacktestListPage.tsx:69-87` 不同状态返回不同顶层元素），`.dashboard-panel` 选择器在这些状态不命中，标题与内容间距塌缩为 0px / 20px（`.feedback-message` / `.dashboard-alert` 的 `margin-top: var(--spacing-20)`）。`> :not(.page-heading)` 覆盖 page-heading 之外的所有直接子元素，三种状态全命中；specificity (0,2,0) 高于 `.feedback-message` / `.dashboard-alert` / `.empty-state` 的 (0,1,0)，能覆盖其现有 `margin-top`。SignalListPage 所有状态都返回 `dashboard-panel`（`SignalListPage.tsx:110-111`，EmptyState / FeedbackMessage 在其内部），`> :not(.page-heading)` 行为与 `.dashboard-panel` 等价，统一选择器仅为对称与前瞻。仍按页面限定 `.signal-list-page` / `.backtest-list-page` 而非宽 `.list-page`：后者会命中 Walk-forward 列表页自身的 `dashboard-panel`（`WalkForwardListPage.tsx:216`，该页 wrapper 为 `list-page walk-forward-list-page`），经 margin 合并吞掉 run-trigger 的 `margin-bottom: var(--spacing-16)`，与 D3 保留该 16px 的意图矛盾。
- **备选**：`.list-page .dashboard-panel`（否决——命中 Walk-forward 列表页次要 panel，破坏 D3）；`.list-page:not(.walk-forward-list-page) .dashboard-panel`（否决——`:not(.walk-forward-list-page)` 依赖具体页面类，脆弱且不如显式两页选择器清晰）；`calc(var(--section-gap) * 0.5)`（否决——违反 spacing 契约的 SHOULD）；24px / 32px（否决——用户已确认 48px，且与 Dashboard 对齐）；仅 `.dashboard-panel` 不覆盖空状态（否决——BacktestListPage 空状态下标题与 EmptyState 间距塌缩，实施时人工确认发现 vela.db 中 `backtest_run` 0 行、列表为空渲染 EmptyState，间距失效）；显式列举 `.dashboard-panel, .empty-state, .feedback-message`（否决——冗长，且新增内容类型需手动加，不如 `:not(.page-heading)` 通用）。

### D2: 详情页章节标题规则挂 `.holdings-section h2`，规格对齐 h3
- **选择**：新增 `.holdings-section h2`，声明 `color / font-family / font-size / font-weight / letter-spacing / line-height / margin: 0 0 var(--spacing-16)`。与现有 h3 使用同一套 token，仅 `margin-bottom` 用 16px。现有 h3 规则分两条：`.holdings-section h3`（`styles.css:1309-1314`，含 `color / font-size / line-height / margin: 0 0 var(--spacing-12)`）与 `.detail-page .holdings-section h3`（`styles.css:1316-1320`，补 `font-family / font-weight / letter-spacing`）。新 h2 规则把全部属性合并到单条 `.holdings-section h2`（不挂 `.detail-page` 作用域）——因 `.holdings-section` 内的 `h2` 仅出现在 Walk-forward Detail（`WalkForwardDetailPage.tsx:121/127/139/160/333/365`，该页为 `.detail-page`），作用域与否在当前代码库下功能等价；单条规则比照搬 h3 的"基础 + `.detail-page` 覆盖"二段式更简单。
- **理由**：与现有 h3 token 体系一致，最小侵入；16px 让标题与正文（`detail-note` margin-bottom 16px）形成协调节奏，消除默认 `margin-block: 0.83em`（≈20px）的失控。
- **备选**：只加 `margin` 不动字体（否决——h2 的 bold 700 与设计体系 510 字重不一致，需一并修正）；`margin: 0 0 12px`（否决——与 h3 完全同规格会让 section 级标题偏挤）；照搬 h3 的二段式拆分（否决——当前 h2 仅存于 detail 页，拆分属过度设计）。

### D3: 不修改 `.walk-forward-run-trigger` 现有 margin-bottom
- **选择**：仅补充 `margin-top: var(--space-xl)`，保留 `margin-bottom: var(--spacing-16)`。
- **理由**：`web-frontend-app` "Walk-forward list page provides run trigger" 场景已固化 `margin-bottom: var(--spacing-16)` 的契约，不破坏现有场景；标题间距由 margin-top 承担。

## Risks / Trade-offs

- [宽选择器 `.list-page .dashboard-panel` 会误命中 Walk-forward 列表页自身的 `dashboard-panel`] → Walk-forward 列表页 wrapper 为 `list-page walk-forward-list-page` 且其 `dashboard-panel`（`WalkForwardListPage.tsx:216`）是次要元素（首个内容元素是 `walk-forward-run-trigger`）。宽选择器经 margin 合并会吞掉 run-trigger 的 `margin-bottom: var(--spacing-16)`，破坏 D3。已通过 D1 把选择器收窄为 `.signal-list-page > :not(.page-heading), .backtest-list-page > :not(.page-heading)` 规避；Dashboard 页为 `.dashboard-page`，本就不被命中。
- [BacktestListPage 空 / loading / error 状态下首个内容元素非 `dashboard-panel`] → BacktestListPage 不同状态返回不同顶层元素（`BacktestListPage.tsx:69-87`：loading → `FeedbackMessage`、error → `FeedbackMessage.dashboard-alert`、empty → `EmptyState`、success → `dashboard-panel`）。最初的选择器 `.dashboard-panel` 在非 success 状态不命中，标题与内容间距塌缩为 0px / 20px。实施时人工确认发现 vela.db 中 `backtest_run` 0 行、列表为空渲染 EmptyState，间距失效；已改用 `> :not(.page-heading)` 覆盖所有状态。SignalListPage 所有状态都返回 `dashboard-panel`（EmptyState / FeedbackMessage 在其内部），不受影响。
- [`:not(.page-heading)` 会命中 section 下所有非标题直接子元素] → 当前 SignalListPage / BacktestListPage 的 section 下只有 page-heading 与单个内容元素（dashboard-panel 或状态组件），`Pagination` 在 `dashboard-panel` 内部非 section 直接子元素，故只命中首个内容元素。若将来在 section 下新增多个直接子元素，都会被加 `margin-top: var(--space-xl)`——属期望行为（标题下内容均应与标题保持 48px），多 panel 并排应自行包裹容器。
- [`.holdings-section h2` 影响 Signal / Backtest Detail 中现有 h2 用例] → 当前详情页 h2 仅 Walk-forward Detail 使用（Backtest / Signal 用 h3）；新规则不会改变 h3 渲染。实施时 grep 确认。
- [h2 浏览器默认 `margin-block-start` 与新增 `margin` 冲突] → 新增规则显式声明 `margin: 0 0 var(--spacing-16)` 覆盖默认值，无级联残留。

## Migration Plan

1. 在 `styles.css` 做三处规则改动：新增 `.signal-list-page > :not(.page-heading), .backtest-list-page > :not(.page-heading) { margin-top: var(--space-xl) }`、为 `.walk-forward-run-trigger` 补充 `margin-top: var(--space-xl)`（保留其 margin-bottom）、新增 `.holdings-section h2` 规则。
2. 更新 delta specs（`design-system` ADDED、`detail-page-typography-consistency` MODIFIED）。
3. 运行 `openspec validate --strict` 与完整 Web gate（lint / lint:css / typecheck / test / build）。
4. 人工确认三个列表页与 Walk-forward Detail 页面间距。
5. 回滚 = 撤销上述三处改动（删除两条新规则、移除 run-trigger 新增的 margin-top）+ 撤销 delta spec；无数据迁移。

## Open Questions

- 详情页 `h2`/`h3` 层级统一（Walk-forward 用 h2、Backtest/Signal 用 h3）是否值得单独 change 处理？（当前不阻塞本 change。）
