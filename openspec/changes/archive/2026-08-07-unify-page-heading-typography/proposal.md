## Why

Dashboard 页面的标题（`.dashboard-heading h1`）使用 `var(--text-heading-sm)`（32px），而其他所有页面（Signals / Backtests / Walk-forwards 的列表页与详情页、ETF Detail）共用 `.page-heading h1` 基础规则，解析到 `var(--text-heading)`（48px）。同一层级的结构元素（页面主标题）在不同页面出现两种字号，且现有 spec（`design-system` 的 dashboard heading 阶梯、`detail-page-typography-consistency` 的跨页面一致要求）与实际实现互相矛盾，需要一次收敛。

## What Changes

- 将 `.page-heading h1` 基础规则的字号从 `var(--text-heading)` 统一为 `var(--text-heading-sm)`，并同步 `letter-spacing`（`--tracking-heading-sm`）与 `line-height`（`--leading-heading-sm`），使全站页面主标题与 Dashboard 当前视觉一致。
- 删除 `.dashboard-heading h1` 对字号、字距、行高的覆盖规则（基础规则已统一，覆盖不再产生差异），保留 `.dashboard-heading` 的布局属性（flex、间距、max-width）。
- 审查并同步 `@media (width <= 720px)` 中对 `.page-heading h1` 的覆盖，使其与新的统一基准一致，避免移动端出现与桌面端矛盾的字号。
- 更新 `design-system` spec：将 "Dashboard heading uses a discrete responsive ladder" 需求改为全站 `page-heading h1` 统一使用 `--text-heading-sm`，移除 48/64/72px 阶梯要求（该要求与当前实现及本 change 的目标冲突）。
- 更新 `detail-page-typography-consistency` spec：将标题一致性场景从 Detail 页面（描述为 `h2`）与 Dashboard（`h1`）扩展为全站所有 `page-heading h1` 页面，并明确统一尺寸为 `--text-heading-sm`；修正场景中 `h2`/`h1` 的标签描述与实际实现（全部为 `h1`）的偏差。

## Capabilities

### New Capabilities

（无新能力引入。）

### Modified Capabilities

- `design-system`: "Dashboard heading uses a discrete responsive ladder" 需求被替换为全站 `page-heading h1` 统一使用 `var(--text-heading-sm)`（32px），删除 48/64/72px 三级响应式阶梯要求。
- `detail-page-typography-consistency`: 标题一致性范围从 "Signal Detail / Backtest Detail / Dashboard" 扩展为全站所有渲染 `page-heading h1` 的页面（含列表页与 ETF Detail / Walk-forward Detail），统一尺寸为 `var(--text-heading-sm)`；修正场景中 Detail 标题标签 `h2` 与实际实现 `h1` 的偏差。

## Impact

- `apps/web/src/styles.css`：`.page-heading h1` 基础规则字号/字距/行高；`.dashboard-heading h1` 覆盖规则删除；`@media (width <= 720px)` 内 `.page-heading h1` 覆盖同步。
- 受影响页面（视觉上标题字号从 48px 变为 32px）：`SignalListPage`、`SignalDetailPage`、`BacktestListPage`、`BacktestDetailPage`、`WalkForwardListPage`、`WalkForwardDetailPage`、`EtfDetailPage`。`DashboardPage` 视觉不变。
- 测试：`DashboardPage.test.tsx`、`SignalListPage.test.tsx` 等页面测试可能断言 `h1` 文本内容（不变）；若存在样式断言需同步。运行完整 Web gate（lint、lint:css、typecheck、test、build）验证。
- 文档：`openspec/specs/design-system/spec.md`、`openspec/specs/detail-page-typography-consistency/spec.md` 两处 spec 更新，与实现保持一致。
