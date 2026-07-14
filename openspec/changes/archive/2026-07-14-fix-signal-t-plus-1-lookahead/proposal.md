## Why

`portfolio_holdings.py` 用 `signal_date <= trade_date` 选取持仓信号，导致 `signal_date = T` 的信号（用**截至 T 日收盘**的价格算出，T 收盘后才可知）在 T 当日就生效，吃到了 T 日收益。回测净值由这些持仓真实计算得出（`strategy_equity_curve.py:74,203`），因此 `total_return` / `Sharpe` / 最大回撤全部被前视偏差抬高。这是回测正确性的硬伤，必须修。

## What Changes

- **BREAKING** 修改信号生效时点：`portfolio_holdings.py:48` 的 `signal_date <= trade_date` 改为 `signal_date < trade_date`。信号严格在其 as-of 日之后（T+1）才对持仓生效。
- 信号自身当日：若有前置成功信号则 carry-forward 旧仓位；若为最早信号则空仓（cash）。需要换仓时，新权重从 T+1 起生效。
- 重写 `packages/core/tests/test_portfolio_holdings.py` 中将"当日生效"固化成断言的用例，使其断言 T+1 语义；同步重写 `packages/core/tests/test_strategy_equity_curve.py` 中通过 `signal_date` 布局间接固化 T+0 的用例（`signal_date` 整体前移 1 天，断言数值不变）。
- 已落库的回测结果因此变更而失真：标记为待重跑（用户将全量重跑），本 change 不做 DB migration。

## Capabilities

### New Capabilities
<!-- 无新增能力 -->

### Modified Capabilities
- `portfolio-holdings`: 持仓选取的生效时点从"信号当日及之后"改为"严格晚于信号 as-of 日（T+1 起）"。这是需求级行为变更，对应 delta spec。

## Impact

- **代码**：`packages/core/src/vela_core/portfolio_holdings.py:48`（一行条件变更）；`strategy_equity_curve.py` 仅消费快照，无需改动（其"当天权重 × 当天收益"模型在 T+1 约定下自洽）；查询边界 `portfolio_holdings.py:69` 的 `signal_date <= through_date` 经验证安全，无需改动。
- **测试**：`packages/core/tests/test_portfolio_holdings.py` 中 5/6 个用例断言了旧语义，需重写为 T+1；`packages/core/tests/test_strategy_equity_curve.py` 通过 `calculate_strategy_equity_curve` 间接依赖 T+0 语义，7 个用例会变红、另有 4 个数值碰巧不变但语义已偏，需将其 `_add_signal` 的 `signal_date` 整体前移 1 天（`trade_dates`/价格/断言不变，数值零变更）；`test_backtest_runner.py` 已 mock `calculate_portfolio_holdings` 与 `calculate_strategy_equity_curve`，不受影响。
- **数据**：`vela.db` 中现存的历史回测 run 数字偏高，需重跑刷新（运营动作，非本 change 范围）。
- **前提约束**：历史回测中所有信号 `generated_at` 被压成运行起始时刻（`backtest_runner.py:163`），故 `generated_at` 不可作 T+1 锚点，`signal_date` 是唯一可用的 as-of 锚点（`strategy_signal_generation.py` 的 `_prices_through` 以 `price.trade_date <= signal_date` 截断价格序列，证实 `signal_date` 为数据截至日）。
