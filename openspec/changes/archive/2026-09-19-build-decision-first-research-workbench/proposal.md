# Proposal: build-decision-first-research-workbench

## Why

Vela 前端目前是按"产物类型"组织的：Dashboard 是一个安装/运维控制台，Signals / Backtests / Walk-forwards 是三个并列的历史列表。研究判断（我该持有什么、策略是否有效、是不是过拟合）需要用户在四个页面之间自行拼装。

更严重的是，"当前状态"这一研究前提完全没有呈现：

- 本地行情数据截至 `2026-08-07`，而 Dashboard 最新 Signal 是 `2024-12-31` 的信号。两者相差近 20 个月，界面上没有任何提示——用户看到 "Signal #307 / Result rebalance" 会误以为它是当前指令。
- 最新 Backtest（`2019-01-01`–`2024-12-31`）只显示裸的 `Total return -17.34% / Max drawdown -41.85% / Sharpe -0.154`，没有任何基准对照，无法判断这是好还是坏。
- 唯一的稳健性证据（Walk-forward OOS）在 Dashboard 上完全不存在；Walk-forward 列表中那条 `queued` 记录的状态也不在任何首屏可见。
- 首屏被 Market data（11 行 ETF 清单）、Strategy（很少变化的动量窗口/权重参数）和 Operations（bootstrap / fetch / run backtest 表单）占据——这些是*参考信息与运维动作*，不是研究判断。

本次变更把 Dashboard 重组为五层 decision-first 研究路径：**当前状态 → 最新 Signal → 策略表现 → OOS 稳健性 → 深度证据**。所有既有面板、动作、金融语义与数值格式化都被保留，只是退到决策层之后。

## What Changes

### 1. Dashboard 首屏改为五层研究路径（前端）

按顺序渲染五个决策层，每层只呈现该层判断所需的事实，并链接到完整证据：

| 层 | 内容 | 数据来源 |
|---|---|---|
| L1 当前状态 | 行情数据截止日、Signal 日期与滞后、最新回测区间、OOS 证据状态；以及唯一的"下一步动作"提示 | 既有 dashboard 聚合的日期字段 |
| L2 最新 Signal | 目标持仓表（交易所/代码/名称/目标权重/排名/得分/fallback）、结果、是否 fallback、**provenance（source + 产出它的回测 run）** | 新增 `latest_signal.positions` / `source` / `backtest_run_id` |
| L3 策略表现 | 四个 headline 指标 + 对 Primary Benchmark 的差值（既有 sign-only 差值语义） | 新增 `recent_backtest.benchmarks` |
| L4 OOS 稳健性 | 最新 Walk-forward 运行状态、窗口数、区间；成功时给出跨窗口 OOS 聚合（中位收益/中位 Sharpe/最大回撤/正收益窗口率/基准超额率）与 Generalization Gap 说明行 | 新增 `latest_walk_forward` |
| L5 深度证据 | Signals / Backtests / Walk-forwards / ETF 行情 的钻取入口 | 既有路由 |

L2 的 provenance 不是装饰：聚合读模型里的"最新成功 signal"按 `generated_at` 取，可能（在本机就确实）是某次回测产出的**模拟产物**。不标注它，首屏就等于把 2024-12-31 的模拟持仓当成当前指令呈给用户。因此 L2 必须显示 source，并在 source 为 `backtest` 时说明这些是模拟持仓、同时链到产出它的那次回测。

关键约束：**L1 只做日期事实比较，不在浏览器里重算任何数值**；L3/L4 **不引入评分、评级或 pass/fail 徽章**（与 `walk-forward-results-ui` 的既有边界一致），只呈现 API 已发布的值与符号差值。

### 2. 决策面上每个 artifact 都可归属、且归属可见

五层里展示的每个 artifact 都必须能判断"它是谁的、由哪份配置产生的"：

- `recent_backtest` 与 `latest_walk_forward` 按当前 `strategy_id` 限定（原来 `recent_backtest` 完全不限定策略，而相邻的 signal 精确限定——可能把别的策略的运行说成本策略的表现）；`config_version` 不作为过滤条件，因为同策略跨版本运行是可比较的证据。
- 不过滤的维度必须显示出来：L3 显示运行的 `config_version`；L2 显示 signal 的 `source`，并在 source 为 `backtest` 时说明这些是模拟持仓、链到产出它的那次运行。
- 文案不得超出事实：无动作提示只能声称它支持得起的状态。

### 3. 既有面板降级为参考与运维区（前端）

Market data（含 `.etf-row-list` ETF 清单，`market-data-etf-visibility` 契约不变）、Strategy 参数、Operations 全部保留原有内容与行为，移到五层之后，并把面板标题改为 `web-frontend-app` 已经规定但当前未实现的标签组合（`Market`/`Price data`、`Strategy`/`Parameters`）。

### 3. Dashboard 聚合读模型扩展（后端，纯增量）

`GET /api/dashboard` 在既有字段不变的前提下新增：

- `latest_signal.positions[]`（含名称/权重/排名/得分/fallback）
- `latest_signal.source` + `latest_signal.backtest_run_id`（provenance）
- `recent_backtest.annualized_return` + `recent_backtest.benchmarks[]`（窄投影：key/name + 4 个指标 + 2 个差值，不含基准净值曲线）
- `latest_walk_forward`（可空：运行级字段 + 成功时的窄 OOS 证据投影）

### 4. Eager 预算按实测修订

当前 `eagerApplication` 实测 39,964 / 40,000 raw bytes（仅剩 36 字节），`lazyJavaScript` 69,995 / 70,000，`totalJavaScript` 339,146 / 340,000。五层首屏必然增加 eager 代码，因此本次变更按**实测值**修订 `web-route-code-splitting` 中 pin 住的预算上限，并把实测证据记录在 `bundle-evidence.md`。修订幅度以实测为准，不做预留性抬升。

## Capabilities

### New Capabilities

- `research-workbench-ui`：Dashboard 的 decision-first 五层信息架构、L1 状态事实（含滞后语义与"不伪造当前性"）、L2 目标持仓、L3 基准对照差值、L4 OOS 证据边界（无证据时如实说明、不伪造）、L5 钻取入口，以及响应式/可访问性要求。

### Modified Capabilities

- `dashboard-aggregation`：首屏聚合读模型新增 `latest_signal.positions` / `source` / `backtest_run_id`、`recent_backtest.annualized_return` / `benchmarks`、`latest_walk_forward`（全部为增量字段，既有字段与语义不变）。
- `web-frontend-app`：修订 "Walk-forward presentation does not expand Dashboard"——Dashboard 现在允许呈现**紧凑的 OOS 稳健性层**（运行状态 + 跨窗口聚合事实 + 指向 Walk-forward 详情/列表的链接），但仍不得在 Dashboard 上复制完整证据、不得给出评分或 pass/fail；另外把 panel 标签一致性要求落到实现。
- `web-route-code-splitting`：按本次实测修订 eager / initial / total（及必要时 lazy）预算带。

## Impact

- **前端**：`apps/web/src/pages/DashboardPage.tsx` 重组，L2/L3/L5 作为其局部组件实现；新增 `ResearchStatusSection.tsx`（L1）、`OosRobustnessSection.tsx`（L4）、`researchWorkbench.ts`（纯函数）、`panelHeading.tsx`（从 DashboardPage 抽出的标题原语）；`api/client.ts` 增补类型；`backtestFormatters.ts` 接收从 `DecisionSummarySection.tsx` 提升出来的共用差值格式化函数；`styles.css` 增补决策层样式（复用既有 `dashboard-panel` / `panel-heading` / `compact-list` / `metric-row` / `holdings-table` / `status-pill` / `operation-link`）。
- **后端**：`packages/core/src/vela_core/dashboard_aggregation.py` 新增三个投影并补 `annualized_return`；`packages/core/src/vela_core/walk_forward/query.py` 抽出共用的「最新 run」排序；`apps/api/src/vela_api/schemas.py` 新增响应模型。
- **契约与门禁**：`check-bundle.mjs` 预算值与 `web-route-code-splitting` spec 同步修订；新增 `bundle-evidence.md` 记录实测。
- **明确不改**：策略配置、信号生成、回测与 walk-forward 的计算、持久化、CLI 行为；`dashboard-aggregation` 既有字段；`market-data-etf-visibility` 的 ETF 行渲染契约；`walk-forward-results-ui` 的"不评分"边界；所有既有路由与列表页。
