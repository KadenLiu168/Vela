## Why

Dashboard 卡片内的 typography 不统一：当前卡片正文 13px / 行高 1.2 既偏小也偏挤；同一视觉角色（label / value / 主数值）在 Dashboard 与 Detail 页之间存在 2px 之差；eyebrow、status pill 与 label 同尺寸、同字距却互不区分；字号 token 之间普遍差 1–2px，缺乏清晰阶梯；同时整个 web 前端只使用 Inter Variable + JetBrains Mono 两族，缺少 display 级字体带来的视觉个性。

## What Changes

- 在 `apps/web/src/styles/tokens.css` 新增卡片级 typography token 阶梯：`--card-meta-size/leading`、`--card-body-size/leading`、`--card-emphasis-size`、`--card-display-size`，每个尺寸拥有对应的 `--leading-*` 与 `--tracking-*` token。
- 新增 `--font-display` 字体族 token 并加载一款具有编辑感的 open-source display 字体（候选 `Geist`、`Departure Mono` 或自托管免费几何体如 `Manrope` variable）作为 panel-heading / page-heading 的视觉升级。
- 调整 Dashboard 卡片正文从 13px / 1.2 升至 14px / 1.5，提升呼吸感。
- 调整 Dashboard 卡片主数值（`.panel-primary`、`.metric strong`）从 24px 升至 28px，配合 `font-variant-numeric: tabular-nums` 与轻微负字距。
- 调整 eyebrow / status pill / label 为统一的"11px / semibold / uppercase / 0.04em tracking"，让徽章与 label 在小字号下依然清晰。
- 调整 `.backtest-run-form` form label / input 与 Dashboard 卡片一致（label = 11px uppercase，input = 14px regular）。
- 所有 line-height 通过 `--leading-*` token 引用，符合 `design-system` 的现有合同。
- 通过 `same-change migration` 在 `tokens.css` 声明新 token，并把旧 token（若不再被消费）在同一 change 内迁移。
- 解除 `detail-page-typography-consistency` 中"Dashboard 页面 typography 保持原样"条款，建立 Dashboard 与 Detail 在卡片 label / value 视觉上的真正统一。
- 删除 `.dashboard-page .compact-list dt` 等仅用于"硬抵抗 detail 规则泄漏"的覆盖规则，让 detail 与 dashboard 真正共享一套 `.compact-list` 样式。

## Capabilities

### New Capabilities

- `card-type-scale`：定义卡片级 typography 阶梯（meta / body / emphasis / display），包括每个尺寸的 `--leading-*` 与 `--tracking-*` token，以及 `--font-display` 字体族；明确 Dashboard 与 Detail 页面在 label / value 字号 / 字重 / 字距 / baseline 上完全一致；规定 eyebrow 与 status pill 的统一规则。

### Modified Capabilities

- `design-system`：在 typography scale 中注册新增的 `--card-meta-*` / `--card-body-*` / `--card-emphasis-*` / `--card-display-*` 与 `--tracking-meta` / `--tracking-numeral` 与 `--font-display` token；新增"line-height 必须来自 `--leading-*` token"的合同补充条款；新增"卡片正文必须 14px / 1.5"的 size 阶梯合同；"card primitives 必须用 `--card-*` token"条款扩展为强制要求 `.dashboard-panel` 与 `.detail-page .dashboard-panel` 使用 `--card-padding-y` 而非裸 `--spacing-20`。
- `detail-page-typography-consistency`：删除"Dashboard 页面 typography 保持原样"requirement 及其 scenario；将"Dashboard 页面 typography 与合并前完全一致"反转为"Dashboard 与 Detail 页面在 compact-list、panel-primary、page-heading、holdings 标题上的视觉一致"，并要求 baseline 对齐同样覆盖 Dashboard 的 compact-list。

## Impact

- 受影响的 CSS 文件：`apps/web/src/styles/tokens.css`（新增 / 调整 token）、`apps/web/src/styles.css`（重写约 12 条 class 规则、删除 3–4 条 dashboard 作用域覆盖规则）
- 受影响的字体资源：`apps/web/public/fonts/` 新增一款 display woff2 文件
- 受影响的 HTML：`apps/web/index.html`（preload 新字体）、`apps/web/src/styles.css`（新增 `@font-face` 规则）
- 受影响的 React 组件：仅在 strategy_id / panel-primary 内容超长时可能需要在 `DashboardPage.tsx` 追加 `text-wrap: balance` 或 `overflow-wrap: anywhere`；其余组件不需要改动
- 受影响的 spec：`design-system`（token 注册 + 条款强化）、`detail-page-typography-consistency`（Dashboard 同步）
- 不修改 backend / 不修改 API / 不新增 npm dependencies（字体自托管）
