## 1. Schema（strategy_config.py）

- [ ] 1.1 放开 `TrendFilterConfig`：`moving_average_days: Literal[60, 120, 250]`、`price_relation: Literal["above", "below"]`（保留 `frozen=True`）

## 2. 移动均线模块（market_price_moving_average.py）

- [ ] 2.1 `calculate_market_price_moving_average` 新增必填关键字参数 `window: int`，`.limit(window)` 替代 `MOVING_AVERAGE_WINDOW`
- [ ] 2.2 护栏 `len(prices) < window or prices[0].trade_date != as_of_date` 与均价 `sum(...) / Decimal(window)` 随 `window` 参数化
- [ ] 2.3 `MarketPriceMovingAverage`：字段 `ma_120d` 改名 `ma`，新增 `window: int` 字段
- [ ] 2.4 移除 `MOVING_AVERAGE_WINDOW` 常量

## 3. 趋势过滤（trend_filter.py）

- [ ] 3.1 删除 `moving_average_days == 120` / `price_relation == "above"` 字面量守卫
- [ ] 3.2 以 `config.trend_filter.moving_average_days` 为 `window`、`config.trend_filter.price_relation` 为 `relation` 驱动比较：`above` 用 `>`、`below` 用 `<`（严格，等值不通过）
- [ ] 3.3 调用 `calculate_market_price_moving_average(..., window=window)`，`TrendFilterResult.moving_average` 取 `moving_average.ma`

## 4. 测试改写与扩展

- [ ] 4.1 改写 `test_market_price_moving_average.py`：所有调用补 `window=` 参数、字段 `ma_120d` -> `ma`、断言相应更新；保留 120 日既有用例语义不变
- [ ] 4.2 `test_strategy_config.py`：将 `rejects_unsupported_trend_filter` 的 `("moving_average_days", 60)` 改为 now-unsupported 值（如 `30`）；`("price_relation", "at_or_above")` 保留
- [ ] 4.3 `test_strategy_config.py`：新增 60 / 250 窗口与 `below` 方向的合法用例（`StrategyConfig.model_validate` 成功）
- [ ] 4.4 `test_trend_filter.py`：新增 `below` 方向用例（价格 < 均线通过、> 均线不通过、== 均线不通过）
- [ ] 4.5 `test_trend_filter.py`：新增 60 日窗口用例，断言均线基于最近 60 行而非 120 行（防"用错窗口"变体）

## 5. 验证

- [ ] 5.1 `ruff check` 与 `ruff format --check` 通过
- [ ] 5.2 `mypy` 严格通过
- [ ] 5.3 `grep` 确认 `packages/` 下无遗留 `ma_120d` / `MOVING_AVERAGE_WINDOW` 引用
- [ ] 5.4 全量 `pytest` 通过（默认配置回归 + 新增 below / 60 日用例）
- [ ] 5.5 默认 120 / above 下 `generate_strategy_signal` 选择集与修复前一致（回归断言）
