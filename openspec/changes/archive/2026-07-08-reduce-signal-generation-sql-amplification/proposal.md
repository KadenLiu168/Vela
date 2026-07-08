## Why

`generate_strategy_signal` 在每次调用时为每个 active ETF 无条件发起 2 次 `MarketPrice` 查询（趋势过滤的当前价位 + 移动均线窗口），对通过趋势过滤的 ETF 再发起 1 次（动量窗口）。`generate_historical_strategy_signals` 对每个 rebalance 日都重新走一遍同样的流程，导致 5 年 weekly 回测触发上万次 `MarketPrice` 查询，且单 ETF 内三次查询的行集存在层层包含的冗余。这种 N+1 取数模式随 ETF 池扩大线性恶化，是回测路径上最大的 IO 放大点。

## What Changes

- 新增 `load_price_panel`（公开 API），按 `etf_ids × [start_date, end_date]` 单次 `IN` 查询加载价格序列并按 `etf_id` 分组返回，复用现有 `ix_market_price_etf_trade_date` 复合索引。
- 将 `generate_strategy_signal` 改为纯函数：移除 `session` 形参，改吃 `price_panel` / `active_etfs` / `defense_lookup` 三个外部注入依赖，函数内部在内存序列上完成趋势过滤与动量评分。
- 将 `apply_trend_filter` 与 `calculate_momentum_score` 拆分为「纯计算 + DB 取数」两部分；纯计算部分只依赖内存中的 `MarketPrice` 序列，便于单测不依赖数据库。
- 在 `run_backtest` 入口调用一次 `load_price_panel` 覆盖整个回测区间，整段回测复用同一份 panel；`generate_historical_strategy_signals` 接受注入的 panel 而非每次自行取数。
- CLI / API 实时调度路径相应改为「`load_price_panel` → 纯函数 → `persist_strategy_signal`」三段式，单次信号生成对 `MarketPrice` 仅 1 次查询。
- 调整受影响单测为不依赖数据库的纯函数测试；新增对 `load_price_panel` 与「回测端到端 byte-equivalent」的回归测试。
- 不引入进程内或跨进程缓存（任务 3 暂不做）；不修改回测业务语义、不修改 `MarketPrice` 表 schema、不修改 `StrategyConfig` 字段。

## Capabilities

### New Capabilities
- `market-price-panel-loading`: 公开的多 ETF × 时间段 `MarketPrice` 批量加载接口契约，要求按 `etf_id` 分组返回、复用复合索引、不重复 `as_of_date` 行、调用方负责 panel 的复用与生命周期。

### Modified Capabilities
- `strategy-signal-generation`: `generate_strategy_signal` 与 `generate_historical_strategy_signals` 的形参语义与依赖注入要求变更——函数不再持有 `session`，信号计算所需的元数据与价格序列全部由调用方注入；`MarketPrice` 的查询次数约束新增到 requiremenets 中。
- `market-data`: 新增 `load_price_panel` 的契约要求（接口形态、返回结构、复合索引复用、`as_of_date` 不重复等），作为多 ETF 批量读取的一阶公开 API。

## Impact

- 受影响代码：
  - `packages/core/src/vela_core/market_price_query.py`（新增）
  - `packages/core/src/vela_core/strategy_signal_generation.py`（编排函数改纯函数）
  - `packages/core/src/vela_core/trend_filter.py`（拆分为纯计算 + DB 取数）
  - `packages/core/src/vela_core/momentum_scoring.py`（拆分为纯计算 + DB 取数）
  - `packages/core/src/vela_core/market_price_moving_average.py`（拆分为纯计算 + DB 取数）
  - `packages/core/src/vela_core/backtest_runner.py`（入口一次性 panel 加载）
  - `packages/core/src/vela_core/__init__.py`（导出新接口）
  - `apps/cli/src/vela_cli/main.py`、`apps/api/src/vela_api/main.py`（实时路径改造）
  - 受影响单测：`packages/core/tests/test_strategy_signal_generation.py` 等
- 公开 API：`vela_core.generate_strategy_signal` 签名变化（**BREAKING**）：移除 `session` 位置参数，新增 `price_panel` / `active_etfs` / `defense_lookup` keyword-only 入参；同步变化的是 `generate_historical_strategy_signals`。下游消费方（CLI、API、单测）随本 change 一起改造。
- 持久化语义不变：`StrategySignal` / `StrategySignalPosition` 写入逻辑保持原状；策略配置 schema 不变；`MarketPrice` 表结构与索引不变。
- 性能影响：单信号生成对 `MarketPrice` 的查询从「per-ETF 2~3 次」降为「1 次 panel 加载」；5 年 weekly 回测对 `MarketPrice` 的总查询数从约 ~9k 量级降至 1 次 panel 查询；纯函数化降低单测启动开销。