# Design: reorganize-backtest-detail

## Context

Backtest Detail Overview 现状（`apps/web/src/pages/BacktestDetailPage.tsx`，686 行）自上而下为：7 行 run 元数据 → 4 张 hero 卡（Total return / CAGR / Sharpe / MaxDD）→ 19 行单一大比较矩阵（`ComparisonMatrix`，12 绝对 + 8 相对行）→ Distribution Risk（Strategy + 每 benchmark，各一个 disclosure）→ Return Stability（disclosure）→ CSI-300 CAPM（disclosure）→ Equity Curve → Raw Parameters（`<pre>` JSON）。

问题：Equity Curve 埋在 Metrics 之后首屏不可见；19 行矩阵核心指标淹没在 TE/IR/capture 细节中；首屏 7 行元数据与决策无关。目标：让用户约 10 秒判断一次 Backtest 是否值得继续研究，同时保留全部现有深度研究能力。**不新增任何回测计算能力，后端零改动。**

关键数据约束（来自 `apps/web/src/api/client.ts` 类型）：
- `BacktestBenchmark` 已有 `total_return_difference`、`annualized_return_difference`（后端已算）。
- **没有** `sharpe_difference` / `max_drawdown_difference` 字段 —— 需前端减法补齐。
- `parameters_json` 是扁平执行元数据（strategy_id / config_version / type / start_date / end_date / risk_free_rate / 各指标版本号），**不含**策略参数本体（momentum 窗口、top_n 等在 `config/strategy_v1.yaml`，前端不可达）。
- 现有 spec `backtest-results-ui` 含约束 "Null API values SHALL NOT be calculated in the browser" —— 与前端减法存在张力，delta spec 已明确边界。

## Goals / Non-Goals

**Goals:**
- Overview 按用户研究路径重排：快速判断结果 → 查看走势 → 比较 Benchmark → 深入风险分析 → 查看实验配置。
- 首屏 Decision Summary 强化 Strategy 相对 Primary Benchmark 的四项差异（CAGR / Sharpe / MaxDD / Total Return）。
- Equity Curve 前移；Benchmark Comparison 拆核心/Advanced 两级；Distribution Risk / Return Stability / CAPM 归入 Deep Analysis 分区；run 元数据压缩为一行摘要；Parameters 人类可读化 + Raw 折叠保留。
- 拆分组件，页面文件瘦身，测试随组件迁移。

**Non-Goals:**
- 不新增/修改任何后端计算、API 字段、数据库结构。
- 不改 Signals tab 及其懒加载行为。
- 不改 EquityCurveChart、DistributionRiskSection、ReturnStabilitySection、seriesColor 等既有组件内部实现。
- 不展示策略参数本体（parameters_json 里没有，前端无数据源）。

## Decisions

### D1: Primary Benchmark 选取
`csi_300_buy_hold` key 优先（沿用仓库现状惯例 —— CapmSection 已特判此 key），缺失时回退 API 返回的数组第一个 benchmark；数组为空则 Decision Summary 只显示策略四项数值。封装为纯函数 `resolvePrimaryBenchmark(benchmarks)`，可单测。
- **备选**：后端加 primary 标记 —— 更明确，但需后端改动，违反"后端零改动"边界，弃用。

### D2: Sharpe / MaxDD 差异 = 展示层减法
`diff = Number(strategy.x) - Number(benchmark.x)`，仅当两侧均为非 null 数值时计算；任一为 null 则渲染 unavailable 格式化。语义边界（写入 spec）：**这是对 API 已提供数值的纯算术展示，不是金融指标推导**，与矩阵 Best 标记（同为浏览器比较数值）同级。MaxDD 是负值，diff > 0 意味着策略回撤更浅（更好），展示措辞用 "shallower/deeper"（浅/深）而非裸差值。
- **备选**：后端新增 difference 字段 —— 更"正统"，但改动后端 + 需要迁移历史数据，且违背本次"不新增计算能力"的定位，弃用。

### D3: Decision Summary 徽章 = 纯符号规则
四项差异各映射为符号（CAGR/Sharpe/TotalReturn: diff>0 有利；MaxDD: diff>0 有利）：
- 全部非负且至少一项为正 → `Outperforming`
- 全部非正且至少一项为负 → `Underperforming`
- 其余（正负混合）→ `Mixed`
- **有效差异 < 2 项时不显示徽章**，仅呈现数字。
不加权重、不算分。徽章只是把差异符号翻译成人话，数字始终可见。纯函数 `computeVerdict(differences)` 可单测。
- **备选**：加权评分 —— 需要主观权重定义，过度设计，弃用。

### D4: Benchmark Comparison 拆两级
- **核心表（保持展开）**：7 行 —— Total return / CAGR / Max drawdown / Annualized volatility / Sharpe / Sortino / Calmar。列结构 = Metric + Strategy + 每 benchmark 一列。Best 标记逻辑（`comparisonMatrix.ts` 的 `bestCellIndexes`）原样复用。
- **Advanced Metrics（折叠 disclosure）**：最长回撤时长/峰谷/恢复 4 行 + TE / IR / Up-Capture(+count) / Down-Capture(+count) / Total-Return-diff / CAGR-diff 共 10 行。Strategy 相对行（TE/IR/capture/diff）Strategy 单元格保持 `n/a`。
- 无 benchmark 时显示现有 no-benchmark state。

### D5: Deep Analysis = 独立分区，不嵌套大折叠
三个既有 disclosure（Distribution Risk ×N、Return Stability、CAPM）从 Metrics 区移入 `Deep Analysis` 分区，**各自保持独立 collapse**。不加外层大 `<details>` 包裹 —— 嵌套 disclosure 的键盘/a11y 行为复杂且收益低，最小改动达成"降级"。

### D6: run 元数据压缩
首屏一行摘要：`Strategy · 日期范围 · Status`。完整 7 项（含 config version、started/finished at、error message）沉入 Experiment Config 区。Signals 懒加载逻辑不动。

### D7: 组件拆分
```
BacktestDetailPage.tsx          ← 编排：tab 逻辑 + run summary + 组装 4 个 section
DecisionSummarySection.tsx      ← 新：primary 选取 + 差异计算 + 徽章
BenchmarkComparisonSection.tsx  ← 新：核心表 + Advanced disclosure（ComparisonMatrix 逻辑迁入）
DeepAnalysisSection.tsx         ← 新：组装三个既有 disclosure
ExperimentConfigSection.tsx     ← 新：人类可读参数 + Raw 折叠 + 完整元数据
```
纯函数（`resolvePrimaryBenchmark` / `computeVerdict` / 差异计算 / 参数映射）放 `backtestFormatters.ts` 或 section 同目录的纯 helper，与组件分离便于单测。

### D8: 人类可读参数映射
`parameters_json` key → label/format 映射表：
| key | label | format |
|---|---|---|
| `strategy_id` | Strategy | 原样 |
| `config_version` | Config version | 原样 |
| `type` | Strategy type | snake_case → human（如 `dual_momentum` → `Dual momentum`） |
| `start_date` / `end_date` | 日期 | `formatDate` |
| `risk_free_rate` | Annualized risk-free rate | 百分比（0.02 → `2.0%`） |
| `*_metric_version` | 指标版本 | 原样版本文本 |
未知 key 回退 raw key + raw value。Raw Parameters 折叠保留原 `formatParameterSummary` pre 块。

### D9: 测试策略
- 现有 `BacktestDetailPage.test.tsx`（1063 行）按组件迁移：`DecisionSummarySection.test.tsx`（primary 回退、差异计算、徽章边界）、`BenchmarkComparisonSection.test.tsx`（核心/Advanced 拆分、Best 标记、no-benchmark）、`ExperimentConfigSection.test.tsx`（映射、未知 key 回退、Raw 折叠）、页面级测试瘦身为编排/顺序断言。
- fake timers 已知坑（`vi.useFakeTimers()` 卡死 `screen.findByText`）继续规避。

## Risks / Trade-offs

- **[徽章可能被误读为绝对结论]** → 徽章仅基于符号、措辞中性，数字差异始终并排展示；spec 将徽章定义为"sign-derived"，不承诺胜率/统计显著性。
- **[前端减法与既有 "browser SHALL NOT calculate" 约束的张力]** → delta spec 明确边界：减法仅作用于 API 已提供的非 null 数值、无金融推导，与 Best 标记同级；评审以此为据。
- **[1063 行测试大改]** → 按组件分批迁移，每迁移一个 section 即跑该组件测试 + 页面级 smoke。
- **[parameters_json 不含策略参数本体，人类可读化覆盖有限]** → Experiment Config 区如实呈现可映射项，Raw Parameters 保留全部原始信息；如需展示策略参数本体需后端写入，超出本次范围，记为后续方向。
- **[MaxDD 差异负值方向反直觉]** → 展示措辞统一 "shallower/deeper"，测试断言该措辞。

## Migration Plan

纯前端信息架构重构，无数据迁移、无 API 变更。回滚 = revert 对应 commit。实施按 D7 组件拆分顺序推进，每步保持页面可编译、测试通过。

## Open Questions

1. 徽章文案（`Outperforming` / `Underperforming` / `Mixed`）是否满足产品语义？如需中文文案或更保守措辞（如 "Mostly favorable"），实施前定稿。
2. 核心表是否包含 Sortino/Calmar（现定 7 行）？若首屏高度敏感，可缩至 5 行（去 Sortino/Calmar，放入 Advanced）—— 需实施前确认。
