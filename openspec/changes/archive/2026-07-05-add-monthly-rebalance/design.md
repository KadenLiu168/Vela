## Context

当前 `packages/core/src/vela_core/rebalance_dates.py` 只有一个公开函数 `generate_weekly_rebalance_dates(trading_dates)`,按 ISO 周分组取每组最后一个交易日。它被 `generate_historical_strategy_signals` 调用,从而同时驱动:
- CLI / 实时信号生成(用户手动触发)
- 回测(`run_backtest` → `generate_historical_strategy_signals`)

策略配置 `config/strategy_v1.yaml` 当前不包含任何调仓频率参数,`StrategyConfig` Pydantic 模型同样没有对应字段。本次改动引入第二档频率「月频」,并把频率选择提升到配置层。

## Goals / Non-Goals

**Goals:**

- 新增月频调仓日期生成函数,语义与 weekly 完全对称:每个自然月 (year, month) 取该月最后一个交易日。
- 在策略配置中暴露 `rebalance.frequency` 字段,可选 `weekly` / `monthly`,默认 `weekly`。
- 历史信号生成按 `config.rebalance.frequency` 派生调仓日期序列,信号生成和回测同步生效。
- 保持 `generate_weekly_rebalance_dates` 现有签名和语义不变(已有测试 + `__init__` 导出)。
- 旧 yaml 在不更新的情况下行为不变(默认 weekly)。

**Non-Goals:**

- 不引入 biweekly、quarterly 或其他频率。
- 不在配置层支持「每月第 N 个交易日」/「调仓日偏移」/「首次建仓日」等高级选项。
- 不改变 `weekly-rebalance-dates` 既有 spec 要求(weekly 行为完全保留)。
- 不为月频设计独立的回测逻辑(共用同一段代码)。
- 不持久化调仓频率到 `StrategySignal` 模型(它是运行快照,频率由 `config_version` 隐式表达)。

## Decisions

### Decision 1: 平行函数 + 内部 dispatcher

- 新增 `generate_monthly_rebalance_dates(trading_dates)` 与现有 `generate_weekly_rebalance_dates` 平行(各自独立、可独立测试、可独立从 `__init__` 导出)。
- 新增 `generate_rebalance_dates(trading_dates, *, frequency)` 作为内部 dispatcher:按 `Literal["weekly", "monthly"]` 分发。
- 调用点 `generate_historical_strategy_signals` 改用 dispatcher,频率来自 `config.rebalance.frequency`。

**Rationale:** 保留两个具体的生成函数(而不是把 monthly 逻辑塞进 weekly 函数)有两个好处 ——
- 每个函数独立可测,失败时定位更准(weekly 已有 5 个测试用例,monthly 一组独立用例即可,互不干扰)。
- `__init__` 仍可单独导出 monthly 函数,方便外部脚本和未来调用。

**Alternatives considered:**
- *单一函数 + frequency 参数*:把 weekly / monthly 逻辑合并成一个带 `frequency` 参数的函数,函数体内部 if 分支。否决理由:weekly 已有 5 个测试用例基于「无 frequency 参数」签名,合并会破 API;且 monthly 的实现差异(按 ISO 周 vs. 按日历月)用独立函数表达更清晰。
- *策略模式类*:为单一概念(月/周分组)引入类层次结构属于过度设计,Phase 1 范围内不必。

### Decision 2: `Literal` 枚举 + 默认 weekly

```python
class RebalanceConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    frequency: Literal["weekly", "monthly"] = "weekly"
```

**Rationale:**
- `Literal` 在 Pydantic 中直接给出 YAML 校验错误(用户写错就立刻报错,不会无声回退)。
- 默认值 `"weekly"` 保证向后兼容:旧 yaml 不写 `rebalance` 也能加载,行为与现在完全一致。
- 跟现有 `TrendFilterConfig.moving_average_days: Literal[120]` 风格一致。

**Alternatives considered:**
- *StrEnum*:同样可行,Phase 1 项目其他地方没在用,保持现状。
- *必填无默认值*:破坏向后兼容,否决。

### Decision 3: 配置子段 `rebalance: { frequency: ... }` 风格

YAML 用子段结构,跟 `momentum:` / `score_weights:` / `trend_filter:` 等保持一致:

```yaml
rebalance:
  frequency: weekly
```

**Rationale:**
- 跟现有所有逻辑段一致。
- 给将来扩展(例如 `rebalance.weekday: friday`、`rebalance.day_of_month: last`)留出空间而不破坏 yaml 结构。

**Alternatives considered:**
- *平铺到顶层*(`rebalance_frequency: weekly`):更短,但破坏现有结构风格;且将来加配置项时需要重构。

### Decision 4: `__init__.py` 同时导出新函数

`packages/core/src/vela_core/__init__.py` 同步导出 `generate_monthly_rebalance_dates`。

**Rationale:** 跟 `generate_weekly_rebalance_dates` 已有的导出习惯一致;外部脚本和未来命令行可独立调用,不必走 dispatcher 间接路径。

## Risks / Trade-offs

- [Risk] 月频配置下,趋势过滤器 / 动量窗口的统计含义可能与周频不一致(同样是 60 个交易日,在月频下覆盖 ≈ 3 个月,在周频下覆盖 ≈ 12 周)。→ **Mitigation**:本次改动不动 momentum / trend_filter 参数;如果研究上发现月频需要不同的窗口,后续在 `rebalance` 子段里加语义化的派生配置(不在本次范围)。
- [Risk] 跨春节等长假期时,「该月最后一个交易日」可能远离真实月末,导致调仓被推迟。→ **Mitigation**:这是 ETF/A 股市场的固有约束,沿用 weekly 同样的「取实际最后一个交易日」原则,不引入人工日历修正。
- [Risk] 测试遗漏 dispatcher 分支,导致 monthly 静默走 weekly 路径。→ **Mitigation**:在 `test_strategy_signal_generation.py` 显式断言「monthly 频率产出的 signal_date 数量明显少于 weekly」,以及具体日期落在月末。
- [Trade-off] 引入 dispatcher 后,debug 堆栈多一层间接。→ 接受:dispatcher 是单层 if/elif,直接断点即可定位,代价微小。
