## Context

回测净值由 `calculate_portfolio_holdings` 产出的持仓快照与 `strategy_equity_curve` 的真实价格变动相乘得出（`strategy_equity_curve.py:74,203`）。当前选取条件 `signal_date <= trade_date`（`portfolio_holdings.py:48`）让 `signal_date = T` 的信号（用截至 T 收盘价格算出）在 T 当日生效，使 T 日收益被该信号捕获——典型的前视偏差，且直接抬高 `total_return` / `Sharpe` / 回撤。

`signal_date` 在 `strategy_signal_generation.py` 中被明确定义为 **as-of 日**（信号数据截至该日收盘）：docstring（line 72-79）要求 `price_panel` 覆盖 "through `signal_date`"，而 `_prices_through`（line 181-191）以 `price.trade_date <= signal_date` 截断价格序列并注明 "`signal_date` is the latest trading date in scope"。因此 `signal_date` 在回测中必须 T+1 才生效。

## Goals / Non-Goals

**Goals:**
- 消除信号选取中的前视偏差：信号严格在其 as-of 日之后（T+1）才对持仓生效。
- 改动收敛到最小：仅一行条件变更 + 测试重写，不引入日期算术、不动查询边界、不动收益曲线计算。
- 让测试显式断言 T+1 语义，防止该 bug 被重新引入。

**Non-Goals:**
- 不改 `strategy_equity_curve.py` 的收益模型（当前"当天权重 × 当天收益"在 T+1 约定下已自洽）。
- 不引入"信号生效区间"等新数据模型或字段。
- 不做历史回测数据的 DB migration（用户将全量重跑）。
- 不处理实时交易 / 下单执行（Phase 1 范围外）。

## Decisions

### D1. 选取条件用 `<` 而非 `signal_date + 1 day <= trade_date`
离散日期下 `signal_date < T` 严格等价于 `signal_date <= T-1`（即 `signal_date + 1 day <= T`）。两者行为完全一致，而 `<` 是最小改动、无需任何日期加减或日历运算，避免引入 `timedelta` 与周末/假日边界的额外复杂度。**选择 `<`。**

### D2. 保持查询边界 `signal_date <= through_date` 不变
`through_date = max(trade_dates)`（line 39）。修正后某交易日 T 需要的是 `signal_date < T` 的最新信号，其日期必 `<= through_date`，一定被取出。经验证查询边界无需改动，避免无谓改动引入遗漏风险。**保持原样。**

### D3. 不改动 `strategy_equity_curve.py`
收益计算采用"T+1 开盘换仓"约定（Scenario A）：日 T 的收益归到 `snapshot.holdings`（T 日权重）头上，即假设 T 开盘已按 `weights_T` 建仓。`<` 修复后 `weights_T` 来自 T-1 收盘信号（T 开盘前可知），从 T 开盘执行、吃 T 日收益，恰好是 T+1。**两者组合已自洽，无需改收益代码。**

> 一致性说明：base `strategy-equity-curve` spec 的 scenario `Rebalance date uses new holdings` 表述为 "a date with a newer successful strategy signal → that date's daily return uses the newer signal's target holdings"。此处 "date with a newer signal" 应理解为**其快照携带该新信号的交易日**——修复后即信号 as-of 日的 T+1——而非信号的 as-of 日 T。收益代码只消费 `calculate_portfolio_holdings` 产出的快照，而修复后的快照在 T+1 才携带新信号，因此该 scenario 在 T+1 约定下依然成立，无需改动收益代码或其 spec。

**测试影响（代码不改，测试要改）**：`packages/core/tests/test_strategy_equity_curve.py` 直接调用 `calculate_strategy_equity_curve`（内部再调 `calculate_portfolio_holdings`），未做 mock，因此其断言依赖信号生效时点的用例把旧 T+0 语义固化在了 `signal_date` 与 `trade_dates` 的相对布局里。`<` 修复后其中 7 个会变红（rebalance / turnover / cost-rate / entry-cost 等数值断言不再成立），另有 4 个因 cost=0、价格缺失或空仓而数值碰巧不变，但语义已悄悄切到 warmup 空仓、不再守护 T+1。重写策略：将该文件所有 `_add_signal(signal_date=...)` 的 `signal_date` 整体前移 1 天（06-23->06-22、06-24->06-23、06-25->06-24），`trade_dates`、价格、cost、断言一律不动。因为 `calculate_strategy_equity_curve` 从 `trading_dates[0]` 起复利、且 `_load_prices_by_key` 按 `trade_date`（而非 `signal_date`）取价，信号生效日相对曲线整体平移 1 天后所有断言数值不变；entry-cost 类用例（06-24->06-23）仍保持"06-23 空仓、06-24 首次建仓"的 warmup 形态，entry cost 仍落在 06-24。详见 tasks Section 3。

> base `strategy-equity-curve` spec 的测试 scenario `Verify rebalance impact on the equity curve` 本身已表述为 "the date **after** the rebalance uses the newer target holdings"，即已是 T+1 语义；原测试代码实现成 T+0 反而与该 scenario 不符，修复后测试才与之对齐。故 base spec 无需改动，仅重写其测试代码。

### D4. 以 `signal_date` 为唯一 as-of 锚点
历史回测中所有信号的 `generated_at` 被压成运行起始时刻（`backtest_runner.py:163`），无法承载逐信号时序。因此只能以 `signal_date` 作为 T+1 判定锚点，这也是修复落在 `portfolio_holdings.py` 的唯一合理位置。

### D5. 重写而非删除固化旧语义的测试
`test_portfolio_holdings.py` 中 5/6 个用例把"当日生效"写成了断言（含 `changes_on_rebalance_date` 显式断言"再平衡日当天换仓"）。这些是 bug 的回归测试，应重写为 T+1 语义断言（而非删除），使修复可被测试守护。`test_strategy_equity_curve.py` 同样通过 `signal_date` 与 `trade_dates` 的相对布局间接固化了 T+0 语义，按 D3 策略同步重写（信号日前移 1 天、断言不变）。`test_backtest_runner.py` 已 mock `calculate_portfolio_holdings` 与 `calculate_strategy_equity_curve`，不受影响。

## Risks / Trade-offs

- **[已落库回测结果失真]** → 现存 `vela.db` 中的 run 数字偏高。缓解：用户全量重跑；本 change 不做自动 migration，仅在 tasks 标注。
- **[warmup 期空仓 + entry cost 时点推迟]** → 最早信号 `signal_date=T0` 自身日及之前显示 cash；修复前 T0 当日（前视）建仓、equity curve 从 T0 起算且 T0->T1 turnover=0 不扣 entry cost，修复后 T0 空仓、T0+1 首次建仓，entry cost 落在 T0+1（按满仓 turnover 计）。这是消除前视后的正确成本，但短窗口 `total_return` 会因此略降。属正确行为，非风险，但需在重跑后向使用者说明数字变动。
- **[测试红变]** → 修复会使 `test_portfolio_holdings.py` 中 5 个用例与 `test_strategy_equity_curve.py` 中 7 个用例先红。这是预期内的"测试原本在测错误行为"，必须随修复一并重写，不能跳过。
- **[语义误解]** → 若未来有人把 `signal_date` 重新理解为"首个生效日"，`<` 会多后移一天。缓解：spec 明确 `signal_date` 为 as-of 日；测试守护 T+1 语义。

## Migration Plan

- 无 DB schema 变更。
- 部署：合并一行条件变更 + 测试重写即可。
- 数据刷新：全部历史回测 run 需重跑以得到无前视偏差的数字（运营动作，本 change 提供提醒而非自动执行）。
- 回滚：将 `portfolio_holdings.py:48` 改回 `<=` 即可恢复原行为；但回滚会使已重跑结果再次失真，需谨慎。

## Open Questions

无。修复形态、warmup 语义、落库结果处理、收益模型约定四个关键问题已在探索阶段与用户逐一确认。
