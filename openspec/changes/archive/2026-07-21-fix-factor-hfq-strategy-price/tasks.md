## 1. 先补回归测试

- [x] 1.1 在 `test_market_price_upsert.py` 中把冲突行 factor 的断言改为“以传入值覆盖”，并保留插入/更新计数断言；同时覆盖 factor 未变化时仍计为 updated，以及新插入行保留传入 factor。
- [x] 1.2 在 `test_market_data_fetcher.py` 中更新已有 corporate-action mismatch 场景：全量重取后，历史行与新增行都具有 upstream factor；另加 full fetch 覆盖已有行 factor 的测试，并保留 partial fetch 只提交成功 symbol、不能视为完整修复的既有契约。
- [x] 1.3 在 `test_market_price_model.py` 中断言 `strategy_price` 不存在且访问抛出 `AttributeError`。
- [x] 1.4 为 `momentum_scoring`、`trend_filter`、`market_price_returns`、`market_price_moving_average` 与 `etf_price_trend` 各增加或改造一个非恒定 factor 的用例，断言其结果等于以 `as_of_date`/趋势终点为锚的 `forward_adjusted_prices` 结果；趋势端点还须断言 JSON shape 不变且最后一点等于该日 `close_price`。不得只把测试 factor 改成相同值。
- [x] 1.5 在 `test_strategy_equity_curve.py` 增加跨因子变化的相邻持仓区间，断言日收益使用“以区间当前日为锚”的两点投影、不会出现由因子锚不一致造成的假跳变；保留现有持仓、换仓和交易成本断言。
- [x] 1.6 更新 `apps/api/tests/test_etf_prices.py` 的非恒定 factor 用例，断言 HTTP URL、`etf`/`points` JSON shape、升序、range/404/empty/422 契约不变，数值改为以所选窗口最新 trade date 为锚的 forward-adjusted price，且最后一点等于该日 `close_price`。

## 2. 数据与模型层

- [x] 2.1 在 `market_price_upsert.py` 的 `ON CONFLICT DO UPDATE SET` 中加入 `factor_hfq`，并把“append-only / immutable”注释改为因子随同一条 upsert 更新。
- [x] 2.2 更新 `market_data_fetcher.py` 相关注释，明确 mismatch 后的成功全量重取会重写 provider 本次返回的既有 ETF factor 行；不得声称会删除或修复 provider 未返回的历史日期。
- [x] 2.3 从 `models/market_price.py` 的 `MarketPrice` 类删除 `strategy_price` property；不改数据库 schema。

## 3. 迁移消费者

- [x] 3.1 在 `_momentum_score_from_prices`、`_trend_filter_from_prices` 和 `_moving_average_from_prices` 的现有 `as_of_date` 存在性 guard 之后，调用 `forward_adjusted_prices(..., rebalance_date=as_of_date)`，仅使用返回 `.price` 计算结果。
- [x] 3.2 在 `calculate_market_price_returns` 的现有 as-of guard 后，将查询结果转换为升序，调用 `forward_adjusted_prices(..., rebalance_date=as_of_date)`，并在投影结果上计算 20/60/120 行窗口收益；不足窗口仍返回 `None`。
- [x] 3.3 在 `get_etf_price_trend` 中以已解析的最新 `end_date` 为锚投影当前窗口，并从投影值构造趋势点；空窗口和 ETF 不存在的返回契约不变。
- [x] 3.4 在 `strategy_equity_curve` 中保留 `(etf_id, trade_date) -> MarketPrice` 的原始行缓存。`_calculate_daily_return` 仅当一对原始行都存在时，以当前区间日期为锚调用 `forward_adjusted_prices([previous, current], ...)` 后计算该持仓收益；不要把单个归一化 Decimal 放入按日期缓存。
- [x] 3.5 更新受影响 docstring，移除“strategy_price / append-only snapshot”表述；以 `rg '\\.strategy_price\\b' packages apps` 复查零个生产调用。测试中只允许 `test_market_price_model.py` 的负向契约断言访问该缺失属性，不得存在正向计算用途。
- [x] 3.6 将 `apps/web/src/pages/EtfDetailPage.tsx` 的图表 accessible title 从 backward-adjusted 改为 forward-adjusted，并同步 `apps/web/src/App.test.tsx` 的 role/name 断言；不修改图表 geometry、hover 或价格数值，不在前端做二次 adjustment。

## 4. 验证与既有数据修复

- [x] 4.1 对 factor overwrite、property removal、ETF trend scale、equity-curve interval 等可产生数值或结构差异的回归用例，先确认其在对应修复前失败、实现后通过。Momentum/returns 等 ratio 结果因归一化常数相消，迁移证明依赖 property removal、生产调用零 grep、mypy 与测试通过，不强造数值失败用例。
- [x] 4.2 运行 `uv run pytest packages/core/tests/ -x --tb=short`、`uv run ruff check .`、`uv run ruff format --check .`、`uv run mypy --config-file pyproject.toml`。
- [x] 4.3 运行完整 `uv run pytest`，确认 API/CLI 调用方没有遗留 `strategy_price` 访问。
- [x] 4.4 运行 `npm --prefix apps/web run lint`、`npm --prefix apps/web run lint:css`、`npm --prefix apps/web run typecheck`、`npm --prefix apps/web run test`、`npm --prefix apps/web run build`，确认仅文案语义变化且图表交互无回归。
- [x] 4.5 在可恢复的现有本地数据库副本上运行不带 `--incremental` 的 `uv run vela fetch-market-data`；必须得到 `success` 且无 failed symbols，若为 `partial` 则记录已提交的成功 ETF、修复 provider 问题后重试至成功。确认已有 active ETF 行的 factor 可更新，随后运行 `uv run vela fetch-market-data --incremental` 确认常规路径无回归。不得在任务中删除或重建用户的 `vela.db`。
- [x] 4.6 记录 full fetch 只覆盖 active ETFs，inactive ETF 历史不会自动修复；还要记录该重取不会改写既有 `StrategySignal` / `BacktestRun`。如需恢复 inactive ETF 或比较修复后的研究结果，分别通过正常 ETF pool 配置/同步后 full fetch，或由操作者显式重跑选定的 signal/backtest；不直接改库，不自动重写历史记录。
- [x] 4.7 运行 `openspec validate fix-factor-hfq-strategy-price --strict`。
