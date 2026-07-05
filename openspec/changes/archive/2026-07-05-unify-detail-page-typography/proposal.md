## Why

Signal Detail 和 Backtest Detail 是同一层级的"研究工作台"页面（route `/signals/:id?` 与 `/backtests/:id?`，共享 `detail-page` 外壳），但其 `<dl class="compact-list">` 的 label 字段（`<dt>`）在视觉上不一致：

- Signal Detail: 13px (`--text-caption`) + uppercase + letter-spacing 0.04em + line-height 1.2
- Backtest Detail: 12px (`--text-label`) + uppercase + letter-spacing 0.04em + line-height 浏览器默认

这 1px 字号差在 Inter Variable 渲染下肉眼可辨，且与"同层级页面观感一致"的产品期望冲突。

不一致的根因不是数值漂移，而是 CSS 写法上"防御式分叉"：Signal Detail 的样式由 `.signal-detail-page .compact-list dt` 单独承担，Backtest Detail 的样式由 `.detail-page dt` 兜底、`.detail-page .compact-list dt` 仅重置 `margin-bottom`。结果两套规则被分别演化、谁先写谁后写决定最终生效值，长期看是回归源。

2026-07-05 修复的 `fix-backtest-detail-field-alignment` 已经把"Backtest 字段与值纵向对齐"做对，本次工作是其姊妹篇：在不破坏那次修复的对齐效果的前提下，把"label 字号/修饰/line-height"对齐到 Signal 一侧，同时把分叉的两套 CSS 规则合并为一套。

## What Changes

- 将 Backtest Detail `compact-list dt` 的字号、line-height、修饰（uppercase、letter-spacing）统一到 Signal Detail 当前的取值（13px / line-height 1.2 / uppercase / 0.04em）
- 合并下列"成对重复"的 CSS 规则：把 `.detail-page:not(.signal-detail-page) .x` 与 `.signal-detail-page .x` 合并为单条 `.detail-page .x`：
  - `.dashboard-panel`（容器背景、边框、padding）
  - `.panel-primary`（字体族、字号、字重、字距、line-height、margin-bottom）
  - `.compact-list` 容器（`gap`、`margin`、`padding`）
  - `.holdings-section h3`（字体族、字重、字距、line-height）
- 新增 `detail-page-typography-consistency` capability，定义"两个 detail 页面在 `page-heading`、字段 label/value、`holdings-section h3`、表格 th/td 上必须使用同一字号/字距/transform 修饰"的可验证要求
- **不**修改 HTML 结构、JSX 组件树、API 客户端或路由
- **不**调整 Dashboard 页面（`.dashboard-page` 作用域下的样式完全不动）
- **不**调整 metric card、equity-curve、parameter-summary 等 Backtest 独有元素的样式

## Capabilities

### New Capabilities

- `detail-page-typography-consistency`: Signal Detail 与 Backtest Detail 两个 detail 页面在 `page-heading`、字段 label/value、`holdings-section h3`、holdings table 表头/单元格等"同层级元素"上必须使用相同的字号、行高、字距、transform 修饰，差异仅在"各自独有的元素"（如 metric-card、equity-curve、parameter-summary）

### Modified Capabilities

无现有 capability 需求变更。`web-frontend-app` 当前 spec 范围只覆盖 Dashboard bootstrap 行为，未涉及 Detail 页面视觉一致性。

## Impact

- `apps/web/src/styles.css` — 删除若干成对重复的 CSS 规则；统一 `.detail-page .compact-list dt` 的字号与 line-height 到 13px / 1.2
- `apps/web/src/pages/SignalDetailPage.tsx` / `apps/web/src/pages/BacktestDetailPage.tsx` — 组件树不变
- 测试影响：当前前端无视觉回归测试。回归保障依赖 `vitest run` 通过 + 人工浏览器抽样（与 2026-07-05 字段对齐修复的验证方式一致）
