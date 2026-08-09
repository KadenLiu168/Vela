# Design — unify-signal-source-filter-button

## Context

`design-system` 已确立三变体按钮契约（`button-primary` / `button-secondary` / `button-tertiary`）：
- "Buttons follow a three-variant contract"：全站按钮必须是三变体之一，禁止第四种视觉处理；
- "Buttons declare their variant via className"：每个 `<button>` 必须携带精确的 variant className，且 `styles.css` 中按钮视觉规则的选择器必须以 `.button-*` 开头。

此前 `fix-walk-forward-run-trigger-styling`、`unify-dashboard-operation-button-variants` 已把 Walk-forward 列表与 Dashboard 的按钮迁入契约。Signals 列表页的 SOURCE 过滤按钮（`signal-source-filter-button`）是剩余的游离点之一：它与 `backtest-tab`（Backtest 详情页 tablist）共享 `styles.css:709-730` 的 segmented 样式，且没有任何字体规格声明（继承浏览器默认 button 样式）。

## Goals / Non-Goals

**Goals**
- Signals 列表页 SOURCE 过滤按钮接入三变体契约，视觉与 Dashboard / Walk-forward 的 `button-secondary` 一致。
- 为 `button-secondary` 增加 `aria-pressed` 选中态（反色填充），供单选/过滤控件复用。
- 消除 `.signal-source-filter-button` 上的"无字体规格 + 无 variant"状态。

**Non-Goals**
- 不迁移 `backtest-tab`（tablist 语义，保留 segmented 外观）——其统一属后续独立 change。
- 不迁移 `stability-selector-button`、`trend-horizon-button` 等其他游离按钮（独立 change 处理）。
- 不引入新按钮组件 / 不改 `DashboardPage`。
- 不改变过滤交互行为（`aria-pressed`、`?source=` URL 同步、翻页重置均保持不变）。

## Decisions

### D1: 基座采用 `button-secondary` 而非 `button-tertiary`
- **选择**：`SourceFilterButton` className 变为 `signal-source-filter-button button-secondary`。
- **理由**：过滤按钮是带边框的可点控件，与 Walk-forward "Run walk-forward"（secondary）、Dashboard 操作按钮同档；`button-tertiary` 是无边框文字按钮，视觉重量太轻，不适合作为整组过滤器。
- **备选**：tertiary（否决，见上）；保留 segmented 仅补字体（否决——不解决"风格不同"）。

### D2: 选中态挂在 `.button-secondary[aria-pressed="true"]` 上
- **选择**：新增全局规则 `.button-secondary[aria-pressed="true"]` → `background: var(--color-mist); color: var(--color-void); border-color: var(--color-mist)`（反色填充，用户已确认）。
- **理由**：满足 "variant class is the only carrier of visual treatment"——选择器以 `.button-` 开头；语义类名 `signal-source-filter-button` 不再承载任何视觉属性。该规则是通用契约：任何 secondary 按钮携带 `aria-pressed="true"` 都获得选中态，符合按钮契约的可复用性。
- **备选**：`.signal-source-filter-button[aria-pressed="true"]`（否决——选择器不以 `.button-` 开头，违反契约）；保留 iris-violet 紫色填充（否决——用户已确认反色填充，且紫色填充属"第四种视觉处理"）。

### D3: 拆分 `.signal-source-filter-button, .backtest-tab` 共享规则
- **选择**：将共享规则组拆成两条独立规则：`.backtest-tab { ... }` 保留原有全部声明；`.signal-source-filter-button` 不再保留任何视觉声明（视觉交由 `button-secondary` 提供）。
- **理由**：共享规则是"改动 filter 会牵连 backtest-tab"的耦合点；拆分后两个控件可独立演进。
- **风险**：拆分时需逐条核对原共享规则中的 `focus-visible` 声明——filter 按钮的 focus 样式由全局 `:where(a, button, input):focus-visible`（`styles.css:72-75`）兜底，backtest-tab 保留原有 `:focus-visible` 规则即可。

### D4: 保留语义类名 `signal-source-filter-button`
- **选择**：className 保留语义类名 + variant 类名双类名。
- **理由**：测试（`SignalListPage.test.tsx` 通过 `getByRole("button", { name })` 定位，不断言 className）与未来维护可依赖语义类名；契约要求 variant 类名存在，二者并存无冲突。
- **注意**：`.signal-source-filter`（容器，`margin-bottom: 16px`）与 `.signal-source-filter-button`（按钮）两个类名不同，拆分时只动按钮类。

## Risks / Trade-offs

- [`.button-secondary[aria-pressed="true"]` 是全局规则，若未来其他组件在 secondary 按钮上使用 `aria-pressed` 会意外获得反色填充] → 语义上合理（pressed=选中），且当前全站仅 filter 按钮使用该组合；如未来出现冲突，再收敛为作用域规则。
- [拆分共享规则时遗漏 `focus-visible` / hover 声明，导致 backtest-tab 视觉退化] → 拆分后立即对比 backtest-tab 的渲染；实施时保留其全部原声明，仅移除 filter 相关。
- [按钮高度从 `min-height: 44px` 变为 `padding: 12px 20px` 的自然高度，视觉略变矮] → 属统一预期的结果；若用户认为过矮，可在后续 change 中为按钮补充最小高度 token。

## Migration Plan

1. 修改 `SourceFilterButton` className（`SignalListPage.tsx`）。
2. 拆分 `styles.css` 共享规则，新增 `.button-secondary[aria-pressed="true"]`。
3. 更新 delta specs（`design-system`、`web-frontend-app`）。
4. 运行 Web gate（lint / lint:css / typecheck / test / build）与 `openspec validate --strict`。
5. 无需数据迁移；回滚 = 还原两个文件 + 撤销 delta spec。

## Open Questions

- 是否需要为 `button-*` 家族补充统一的最小高度（`min-height`）token，使过滤按钮与操作按钮高度完全一致？（留待后续 change，不在本 change 内决策。）
