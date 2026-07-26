## Why

Vela v1 策略（dual momentum）目前只在单一历史区间内评估一组固定参数，无法判断参数是否过拟合，或其表现能否延续到未参与选参的后续区间。Walk-forward 分析通过滚动训练/测试窗口检验参数稳定性与样本外表现，并通过等权基准提供同区间参照。

## What Changes

- 新增 `walk-forward` 模块，提供按明确日期边界滚动的训练/测试参数搜索与样本外评估能力
- 新增 `vela walk-forward` CLI 命令，通过 YAML 配置驱动整个分析流程，并支持把报告写入文件
- 参数空间由 YAML 定义，框架本身策略无关——换策略不需改 walk-forward 代码
- 搜索阶段从源 SQLite 创建一次性内存快照，训练回测的持久化仅发生在快照内，不膨胀源数据库
- 可选自动跑等权基准（`equal_weight`），输出年化收益差与 Sharpe 差

## Capabilities

### New Capabilities
- `walk-forward-runner`: 滚动窗口编排——切分训练/测试窗，对每个窗口执行参数搜索 → 选最优 → 样本外评估 → 聚合报告
- `parameter-search`: 参数空间定义与网格搜索——从 YAML 读取参数范围，生成有效组合，在训练窗内评估并选出最优参数

### Modified Capabilities
<!-- 无现有 capability 的规范行为发生变化；新模块复用既有 backtest / strategy 契约。 -->

## Impact

- **新增文件**: `packages/core/src/vela_core/walk_forward/` 包（config, window_splitter, parameter_space, runner, report）
- **修改 CLI 集成**: 在 `apps/cli/src/vela_cli/main.py` 注册并执行 `vela walk-forward`
- **新增配置文件**: `config/walk_forward_v1.yaml`
- **不修改**现有 backtest、strategy、signal generation 的行为
- **依赖**: 复用现有 `run_backtest()` 的读写契约及 `load_strategy_config()`、`validate_strategy_config()`
