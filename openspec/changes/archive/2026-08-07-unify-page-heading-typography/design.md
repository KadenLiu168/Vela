## Context

当前全站页面主标题存在两种字号：

- `.page-heading h1` 基础规则（`styles.css:181-189`）解析到 `var(--text-heading)`（48px），服务于所有列表页与详情页（Signals / Backtests / Walk-forwards / ETF）。
- `.dashboard-heading h1` 覆盖规则（`styles.css:203-208`）解析到 `var(--text-heading-sm)`（32px），仅作用于 Dashboard。

同时现有 spec 与实现存在矛盾：

- `design-system` spec 要求 `.dashboard-heading h1` 采用 48/64/72px 三级响应式阶梯，但实现从未如此（当前为 32px 固定值，tokens 亦无响应式定义）。
- `detail-page-typography-consistency` spec 要求 Detail 页面（描述为 `h2`）与 Dashboard（`h1`）标题一致，但实际所有页面均使用 `h1`，且该 spec 不覆盖列表页。

用户决策：Dashboard 当前标题大小（32px）合适，其余页面标题统一对齐到该尺寸。

约束：

- 标题 token（`--text-heading-sm` / `--tracking-heading-sm` / `--leading-heading-sm`）已存在，无需新增。
- 共享结构元素的视觉一致性须由基础规则达成，不引入新的作用域覆盖层（与 `detail-page-typography-consistency` spec 的既有原则一致）。
- 仅 Web 前端改动，不涉及后端与数据库。

## Goals / Non-Goals

**Goals:**

- 全站所有渲染 `page-heading h1` 的页面（Dashboard、Signals、Backtests、Walk-forwards、ETF 的列表与详情页）使用同一字号 `var(--text-heading-sm)`（32px），并配套统一的 `letter-spacing`（`--tracking-heading-sm`）与 `line-height`（`--leading-heading-sm`）。
- Dashboard 视觉保持不变。
- 删除因统一而冗余的覆盖规则与重复的移动端覆盖。
- 同步更新 `design-system` 与 `detail-page-typography-consistency` 两份 spec，使文档与实现一致。

**Non-Goals:**

- 不重构按钮体系（属于独立的 `extract-shared-button-component` change）。
- 不动其他共享结构元素（`.panel-primary`、`.compact-list`、`.holdings-section h3`、`.holdings-table`）的排版——它们已有独立 spec 覆盖且不属于本 change 范围。
- 不调整 `.dashboard-heading` 的布局属性（flex、间距、max-width）。
- 不改变 eyebrow（`.page-heading p`）样式。

## Decisions

### 决策 1：修改 `.page-heading h1` 基础规则，而非逐页添加覆盖

将 `styles.css:181-189` 中 `.page-heading h1` 的 `font-size` 从 `var(--text-heading)` 改为 `var(--text-heading-sm)`，`letter-spacing` 从 `var(--tracking-heading)` 改为 `var(--tracking-heading-sm)`，`line-height` 从 `var(--leading-heading)` 改为 `var(--leading-heading-sm)`。

- 备选：给每个非 Dashboard 页面添加 `.xxx-page .page-heading h1` 覆盖。
- 选择理由：基础规则是单一真源，一次改动覆盖全部 7 个页面；逐页覆盖会新增 7 组作用域规则，违反"共享元素由基础规则达成一致、不引入 descendant 覆盖"的既有 spec 原则，且未来新增页面会再次漂移。

### 决策 2：删除 `.dashboard-heading h1` 覆盖块（`styles.css:203-208`）

基础规则统一到 `--text-heading-sm` 后，该覆盖（font-size/letter-spacing/line-height）与基础规则完全一致，不再产生任何差异。

- 备选：保留覆盖块作为"显式声明"。
- 选择理由：删除后 Dashboard 与其他页面共享同一条规则，杜绝未来单边改动再次造成漂移；`.dashboard-heading` 的布局规则（flex、gap、justify-content、max-width）不受影响，继续保留在 `styles.css:191-197`。

### 决策 3：删除 `@media (width <= 720px)` 中的 `.page-heading h1` 覆盖（`styles.css:2037-2041`）

该覆盖当前将 `.page-heading h1` 设为 `var(--text-heading)`（48px），与基础规则完全重复（tokens 无响应式定义，二者值相同），属冗余规则。统一后若保留，移动端非 Dashboard 页面标题会解析为 48px，与 Dashboard 移动端（32px）不一致。

- 备选：把该 media 覆盖改为 `var(--text-heading-sm)`。
- 选择理由：改后该覆盖与基础规则又完全重复，不如直接删除，保持规则集最小。

### 决策 4：同步更新两份 spec

- `design-system`：将 "Dashboard heading uses a discrete responsive ladder" 需求替换为全站 `page-heading h1` 统一使用 `var(--text-heading-sm)`。原需求的 48/64/72 阶梯与实现及用户决策冲突，属需求变更（MODIFIED）。
- `detail-page-typography-consistency`：将标题一致性场景扩展为覆盖所有 `page-heading h1` 页面（含列表页与 ETF / Walk-forward 详情页），统一尺寸为 `var(--text-heading-sm)`；修正场景中 Detail 标题标签 `h2` 与实际实现 `h1` 的偏差（MODIFIED）。

选择理由：spec 必须与实现保持同步；两份 spec 恰好是本 change 行为变更的权威描述位置，就地修改而非新建重叠 spec。

## Risks / Trade-offs

- 除 Dashboard 外的 7 个页面标题从 48px 变为 32px，视觉层级降低 → 这是用户明确决策的结果（"Dashboard 大小刚好，其余保持一致"）；若后续需要标题更醒目，应在 design-system spec 层统一调整 token，而非恢复单页覆盖。
- 标题在 32px 下对较长文案（如 "Walk-forward History"、"ETF Detail"）可能换行 → 页面标题容器 `max-width: 820px`，32px 单行宽度充足，换行风险低；实现后通过页面测试与截图确认。
- `design-system` spec 的需求替换可能影响依赖该需求的既有测试或校验 → 当前无 active changes，且归档 spec 由本 change 同步更新；实现阶段运行完整 Web gate 与 `openspec validate --strict` 验证。
- 若测试套件存在标题字号相关的快照/样式断言 → 需同步更新；实现阶段先运行测试定位，再决定更新断言或保持。

## Migration Plan

- 纯前端 CSS 与文档改动，无数据库/接口迁移。
- 回滚策略：`git revert` 本 change 的 styles.css 改动并恢复两份 spec 文件即可，改动相互独立、无副作用。

## Open Questions

无。实现前唯一需要确认的移动端行为（720px 以下标题维持 32px 与 Dashboard 一致）已在决策 3 中明确。
