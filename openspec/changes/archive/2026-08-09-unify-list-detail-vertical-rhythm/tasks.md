# Tasks — unify-list-detail-vertical-rhythm

## 1. 样式改动

- [x] 1.1 `apps/web/src/styles.css`：新增 `.signal-list-page > :not(.page-heading), .backtest-list-page > :not(.page-heading) { margin-top: var(--space-xl); }`（Signals / Backtests 列表页标题与首个内容元素间距 48px，覆盖 dashboard-panel / empty-state / feedback-message 所有状态）。选择器用 `> :not(.page-heading)` 而非 `.dashboard-panel`：BacktestListPage 空 / loading / error 状态下首个内容元素是 `EmptyState` / `FeedbackMessage` 而非面板（`BacktestListPage.tsx:69-87`），`.dashboard-panel` 不命中；SignalListPage 所有状态都返回 `dashboard-panel`（`SignalListPage.tsx:110-111`），行为等价。选择器**限定这两个列表页**：Walk-forward 列表页首个内容元素是 `walk-forward-run-trigger`，其标题间距由 1.2 承担；宽选择器 `.list-page .dashboard-panel` 会命中 Walk-forward 列表页自身的 `dashboard-panel`（`WalkForwardListPage.tsx:216`），经 margin 合并吞掉 run-trigger 的 `margin-bottom: var(--spacing-16)`，破坏 D3 保留的 16px 间距
- [x] 1.2 `apps/web/src/styles.css`：`.walk-forward-run-trigger` 补充 `margin-top: var(--space-xl)`，保留现有 `margin-bottom: var(--spacing-16)`
- [x] 1.3 `apps/web/src/styles.css`：新增 `.holdings-section h2` 规则（`color: var(--color-paper)`、`font-family: var(--font-display)`、`font-size: var(--text-subheading)`、`font-weight: var(--font-weight-medium)`、`letter-spacing: var(--tracking-subheading)`、`line-height: var(--leading-subheading)`、`margin: 0 0 var(--spacing-16)`）

## 2. 验证

- [x] 2.1 运行 `openspec validate unify-list-detail-vertical-rhythm --strict` 通过
- [x] 2.2 运行完整 Web gate：`npm --prefix apps/web run lint`、`lint:css`、`typecheck`、`test`、`build` 全绿
- [x] 2.3 人工确认：三个列表页标题与首个内容元素间距 48px——/signals、/backtests 标题→首个内容元素（vela.db 全空时为 `EmptyState`，有数据时为 `dashboard-panel`；loading / error 时为 `FeedbackMessage`，三种状态均需 48px）；/walk-forwards 标题→`walk-forward-run-trigger`；Walk-forward 列表页 run-trigger 与历史表面板间距保持 16px（未被 1.1 命中）；Walk-forward Detail 章节标题（Execution / Aggregated evidence / Window evidence 等）为设计规格且与正文间距 16px
