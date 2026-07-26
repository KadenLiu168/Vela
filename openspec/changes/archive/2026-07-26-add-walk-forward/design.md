## Context

Vela v1 策略（dual momentum）的 `run_backtest(session, config, start_date, end_date)` 会从同一个 SQLAlchemy session 读取 `ETFInfo`、`MarketPrice`、`TradingCalendar`，并在调用方事务内写入信号、回测结果和权益曲线。当前系统缺少参数优化和样本外验证能力——所有参数来自单一 `config/strategy_v1.yaml`，在一个历史区间内一次性评估。

Walk-forward 本质是反复调用 `run_backtest()`：用不同的参数、不同的时间窗口。核心挑战在于：参数空间必须策略无关（不能硬编码 `short_window_days`、`top_n` 等策略特定字段），搜索阶段不能膨胀生产数据库，结果必须可审计。

## Goals / Non-Goals

**Goals:**
- 提供滚动窗口（anchor walk-forward）的训练/测试分离
- 参数网格搜索：训练窗内选最优参数，测试窗做样本外评估
- 参数空间由 YAML 定义，walker 框架完全策略无关
- 搜索阶段使用源 SQLite 的内存快照，不向源数据库写入训练结果
- 可选自动跑等权基准，输出年化收益差与 Sharpe 差
- 独立 CLI 命令 `vela walk-forward`

**Non-Goals:**
- 不实现随机搜索、贝叶斯优化（预留接口，不做实现）
- 不实现多目标优化（Pareto frontier）
- 不实现交叉验证（CV）
- 不修改 `run_backtest()` 或任何现有策略行为
- 不提供 Web UI（仅 CLI + 终端报告）

## Decisions

### 1. 窗口方案：Anchor Walk-Forward

**选择**: 使用配置中的 `start_date` / `end_date` 作为完整分析范围，生成固定长度训练窗（3 年）+ 固定长度测试窗（1 年），按步长（1 年）滚动。这里的 “anchor” 指每个窗口以 `start_date + i * step_years` 为日历锚点；训练窗本身仍是固定长度滚动窗。

**理由**: 对于 ETF 动量策略，市场状态会结构性变化，老数据对预测当前没有帮助。固定窗口各窗口可比，且自动淘汰过时数据。相比 Expanding Window（数据利用率高但早期窗口训练集太小、各窗口不可比），Anchor 更适合这个场景。

**窗口生成逻辑**:
```
给定排序去重后的交易日列表、配置范围 [start_date, end_date] 和
(train_years=3, test_years=1, step_years=1):
  anchor_i    = start_date + i*step
  train 日历窗 = [anchor_i, anchor_i + 3y)
  test  日历窗 = [anchor_i + 3y, anchor_i + 4y)
  仅当 test 日历窗完整落在 [start_date, end_date + 1 day) 时生成窗口。
  每个半开日历窗解析为其中第一个和最后一个实际交易日，再作为
  run_backtest() 的闭区间 start_date/end_date。
```

按年份平移时对 2 月 29 日做目标年份月末截断。最终不足一个完整测试日历窗的尾段丢弃；任一完整日历窗内没有交易日则配置/数据错误，不静默生成空窗口。该定义避免训练和测试共享边界交易日。

### 2. 参数空间：YAML 定义，策略无关

**选择**: 参数空间使用相对于完整策略配置根节点的扁平点号路径（例如 `parameters.momentum.short_window_days`）+ 值列表，框架通过 `merge_into_config(base_config, combo)` 构造完整字典，再调用 `validate_strategy_config()` 自动拒绝无效组合。

**替代方案**: 嵌套 YAML 结构（`momentum: {short_window_days: [20, 40]}`）——框架需要理解策略的嵌套结构，耦合策略细节。点号路径更通用：框架只看到 `name → values` 的映射。

**约束处理**: `ParameterSpec` 自身拒绝空 choice、非正 step、`low > high` 和重复 name；策略字段约束不重复定义。`short < long`、`score_weights` 和为 1.0 等约束由现有策略 pydantic 模型校验。`float_range` 用十进制步进并包含可到达的 high，避免二进制浮点累计误差。未知路径最终会因策略配置 `extra="forbid"` 被拒绝。

**v1 参数空间**（不搜 `score_weights`，缩减搜索空间 + 避免衍生参数 `long = 1 - short` 问题）:
```yaml
strategy:
  base_config: strategy_v1.yaml  # 相对本 walk-forward YAML
window:
  scheme: anchored_rolling
  start_date: 2019-01-01
  end_date: 2024-12-31
  train_years: 3
  test_years: 1
  step_years: 1
objective: sharpe_ratio
parameter_space:
  - name: parameters.momentum.short_window_days
    type: int_range
    low: 20
    high: 100
    step: 20
  - name: parameters.momentum.long_window_days
    type: int_range
    low: 80
    high: 250
    step: 40
  - name: parameters.trend_filter.moving_average_days
    type: choice
    values: [60, 120, 250]
  - name: parameters.selection.top_n
    type: int_range
    low: 1
    high: 3
    step: 1
baseline:
  type: equal_weight
  strategy_id: walk_forward_equal_weight
  version: v1
```

### 3. 搜索阶段持久化：源数据库的内存快照

**选择**: runner 在任何训练回测前，通过 SQLite backup API 把调用方 session 所连接的源数据库复制到一个由单连接 `StaticPool` 持有的 `sqlite+pysqlite:///:memory:` 数据库。快照同时包含 schema、ETF、行情、交易日历及既有引用数据；所有训练回测读写该内存 session，跑完关闭并丢弃。每个组合成功后提交内存事务，失败时回滚该组合，避免一次失败污染后续搜索。最终 OOS 及基准评估才使用调用方提供的真实 session。

**理由**: `run_backtest()` 既读输入又持久化输出，只有空 schema 的内存库会因没有 `MarketPrice` 而失败；仓库中也不存在 `bootstrap.ensure_schema()`。完整 SQLite backup 复用真实输入与当前 schema，同时不改核心回测路径，也不向源库写入数百个训练结果。

**替代方案**: 给 `run_backtest()` 加 `persist=False` 参数——改动核心回测路径，测试覆盖成本高，且 `equity_curve` 计算依赖 `signal_ids`，不持久化需要重构数据流。内存数据库方案零改动，风险更低。

### 4. 优化目标：单目标 Sharpe

**选择**: v1 配置只接受 `objective: sharpe_ratio`。仅 `status == "success"` 且 `sharpe_ratio` 非空的训练结果可参与排序；最高 Sharpe 获胜，并列时按参数组合的 canonical JSON 字典序选择，保证可重复。若一个窗口没有可评分组合，整个命令明确失败且不执行该窗口 OOS。

**理由**: Sharpe 是风险调整后收益，避免选到"高收益但 MDD 也炸"的参数。多目标优化（Pareto frontier）是 P2 的事，当前阶段单目标足够。

### 5. 基准：配置开关，默认启用

**选择**: `baseline` 为包含显式 `strategy_id` 与 `version` 的 `equal_weight` 配置时，每个测试窗自动跑一次等权策略回测，报告输出 OOS 年化收益差和 Sharpe 差；`baseline: null` 时跳过。基准从 base strategy 继承 universe、rebalance、costs、performance，但使用 `parameters: {}` 及其独立身份。

**理由**: 等权只有一种参数组合，跑一个窗口不到 1 秒，不增加实质计算量。超额收益是判断策略是否有效的关键指标。

### 6. 错误处理与持久化身份

**选择**: 单个组合在配置验证或回测中抛出普通 `Exception` 时，回滚该组合的内存事务、记录参数与原因并继续；不会捕获 `KeyboardInterrupt` / `SystemExit`。配置无效、回测异常、非 success 状态或空目标值都计入 skipped 汇总。

每个将写入源数据库的 OOS 配置使用 `wf-<12 hex sha256>` 作为 `version`；hash 输入是移除原 `version` 后的完整有效配置 canonical JSON。相同有效配置复用同一身份，不同有效参数得到不同版本，满足现有 `(strategy_id, config_version)` 不得表示不同行为的契约。最终报告同时记录该 version 与完整最佳参数。基准身份由配置显式提供且不得与被优化策略身份相同。

runner 不提交或回滚调用方的源 session。CLI 沿用仓库 `managed_session` 边界，仅在全部窗口、OOS 和基准均成功后一次提交；任一后续失败会回滚本次命令在源库产生的全部 OOS/基准写入。内存搜索 session 的逐组合提交不受此规则影响，因为快照最终整体丢弃。

### 7. 模块结构

```
packages/core/src/vela_core/walk_forward/
├── __init__.py            # 公开 API: run_walk_forward()
├── config.py              # WalkForwardConfig (pydantic)
├── window_splitter.py     # generate_windows()
├── parameter_space.py     # ParameterSpace, generate_combinations()
├── runner.py              # WalkForwardRunner
└── report.py              # format_report(), aggregate_results()
```

walk-forward 包为新增模块；CLI 入口及 core 公开导出按现有模式做最小接线修改。

### 8. 数据流

```
WalkForwardConfig (YAML, 含 start_date/end_date)
  │
  ▼
WalkForwardRunner.run(session)
  │
  ├─► 从源 session 加载范围内交易日并创建一次内存 SQLite 快照
  ├─► WindowSplitter.generate_windows(trading_dates, configured range)
  │     └─► [(train_start, train_end, test_start, test_end), ...]
  │
  ├─► For each window:
  │     │
  │     ├─► ParameterSpace.generate_combinations()
  │     │     └─► [{"parameters.momentum.short_window_days": 20, ...}, ...]
  │     │
  │     ├─► For each combo (in memory DB):
  │     │     ├─► merge_into_config(base_config_dict, combo)
  │     │     ├─► validate_strategy_config(merged)  ← pydantic 校验
  │     │     ├─► run_backtest(mem_session, config, train_start, train_end)
  │     │     └─► commit/rollback memory transaction; record score or skip reason
  │     │
  │     ├─► best = deterministic argmax(train_sharpe)
  │     ├─► assign deterministic behavior-stable OOS version
  │     │
  │     ├─► run_backtest(real_session, best_config, test_start, test_end)
  │     │     └─► record OOS metrics
  │     │
  │     └─► (optional) run_backtest(real_session, baseline_config, test_start, test_end)
  │
  └─► WalkForwardReport.aggregate(window_results)
        └─► 终端文本报告，并在 --output 提供时写入文件
```

## Risks / Trade-offs

- **[性能] 示例网格为每窗口 225 个组合，3 个窗口共 675 次训练回测**: 单线程执行可能耗时数分钟；对个人研究工具可接受。后续可另行设计并行搜索，当前阶段不做。
- **[SQLite 限定] backup API 绑定当前本地 SQLite 架构**: v1 明确只支持 SQLite；如果未来支持其他数据库，需另行设计只读输入快照。
- **[内存占用] 完整数据库快照包含既有回测输出**: 实现最简单且快照一致，但比只复制三张输入表占用更多内存；对当前个人本地数据库可接受，并在集成测试覆盖源库零训练写入。
- **[参数空间不搜 score_weights]**: 简化了实现（避免衍生参数 `long = 1 - short`），但牺牲了权重分割的搜索。如果后续需要，可加 `derived_params` 声明。
- **[无交叉验证]**: 训练窗内单次 Sharpe 选参可能受噪音影响。但 walk-forward 的多窗口本身就是一种时间序列验证——3 个独立 OOS 窗口会暴露参数不稳定。
- **[OOS/基准会持久化]**: 正常命令会向目标数据库写入每个测试窗的 OOS 与可选基准回测；自动化验收必须使用临时数据库副本，针对 `vela.db` 的真实运行需要另行明确授权。

## Migration Plan

无 schema migration。新增模块、配置和 CLI 接线；回滚时删除新增模块/配置并撤销 CLI 接线即可，现有回测数据保持可读。

## Open Questions

无。v1 的数据库类型、窗口闭开边界、目标指标、并列规则、失败规则、身份生成和基准构造均在本设计中固定。
