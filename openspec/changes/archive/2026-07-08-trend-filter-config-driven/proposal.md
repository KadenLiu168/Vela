## Why

趋势过滤（trend filter）对外宣称可配置 `moving_average_days` 与 `price_relation`，但实现链路用硬编码字面量（`== 120` / `== "above"`）覆盖了从配置读到的值，且 schema 用 `Literal[120]` / `Literal["above"]` 在加载期就把取值锁死——配置项形同虚设。当前默认配置（120 / above）下结果恰好正确，属 latent 缺陷；一旦放开 schema 让配置真正可变，比较逻辑与移动均线窗口两处会先后静默失效：`apply_trend_filter(...).passes_filter` 对所有 ETF 恒为 False，动量 ETF 被全部剔除，信号生成静默退化为防御资产 100% 兜底，且无报错、无日志告警。

## What Changes

- 放开 `TrendFilterConfig` schema 为闭集 `Literal[60, 120, 250]` / `Literal["above", "below"]`，加载期对非法值 fail-fast（与现有"unsupported trend filter 被拒"契约一致，仅扩展合法集）。
- `calculate_market_price_moving_average` 窗口参数化：新增必填 `window` 参数，按请求窗口取价并计算均线；返回字段 `ma_120d` 改名 `ma` 并新增 `window` 字段；移除 `MOVING_AVERAGE_WINDOW` 常量。**BREAKING**（公开函数签名与数据类字段变更）。
- `apply_trend_filter` 删除 `moving_average_days == 120` / `price_relation == "above"` 字面量守卫，真正以 `config.trend_filter` 驱动均线窗口与比较方向（above 用 `>`、below 用 `<`，严格不等）。
- 同步改写 `test_market_price_moving_average.py`（适配新签名与字段名），扩展 `test_trend_filter.py`（新增 below / 60 日窗口用例，断言使用的是 60d 而非 120d 均线）。
- 默认 120 / above 路径逐字节等价（回归保证）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `trend-filtering`: 趋势过滤的移动均线窗口与价格比较方向由配置驱动；不再是写死的 120 日 / above。新增 below 方向与 60 / 250 窗口的过滤行为；等值边界（价 == 均线）在 above / below 下均不通过。
- `strategy-configuration`: `trend_filter` 合法窗口集由 `{120}` 扩展为 `{60, 120, 250}`、合法比较方向由 `{above}` 扩展为 `{above, below}`；集合外取值仍在加载期 fail-fast。

## Impact

- 代码：`packages/core/src/vela_core/{strategy_config.py, market_price_moving_average.py, trend_filter.py}`；测试 `packages/core/tests/{test_market_price_moving_average.py, test_trend_filter.py}`。
- 公开 API：`vela_core.calculate_market_price_moving_average` 签名变更（新增必填 `window` 关键字参数）、`vela_core.MarketPriceMovingAverage` 字段重命名（`ma_120d` → `ma`，新增 `window`）——**BREAKING**；生产侧唯一消费方为 `trend_filter.py`，随本次同步更新，无其他生产读取方。
- 配置：`config/strategy_v1.yaml` 无需改动（120 / above 仍在合法集内）。
- 下游：`strategy_signal_generation.py` 仅读 `TrendFilterResult.passes_filter`，`TrendFilterResult` 形状不变，不受影响。
