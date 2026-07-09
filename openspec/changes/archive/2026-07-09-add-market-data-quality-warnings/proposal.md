## Why

Vela 的数据层只做逐行级校验（缺值、异常价格、OHLC 一致性），缺少批次级校验。`market_price_upsert._deduplicate_market_prices` 对同一 `(etf_id, trade_date)` 采用“后写覆盖先写”——这是 `market-data` 规约强制的行为——重复行被静默折叠，写入值可能与真实值不符且无任何提示。系统从不报错，数据脏只能在事后回溯时才被发现。本变更为数据层引入一个可观测的软信号通道，让重复交易日问题在抓数时即可被看见，而非在亏钱后才发现。

本变更是 Data Quality 校验层的第一阶段（Phase 1）。交易日缺口检测（`detect_trading_day_gaps`）依赖一个尚不存在的交易日历来源，作为独立后续 change 处理，不在本次范围内。

## What Changes

- `DataFetchLog` 新增 `quality_warnings`（nullable `Text`，存 JSON）字段，作为数据质量软信号落点，与硬失败的 `error_message` 分离。
- 新建 `packages/core/src/vela_core/data_quality.py`，提供纯函数 `detect_duplicate_trade_dates(prices)`：统计同一抓取批次内 `(etf_id, trade_date)` 的折叠次数，返回重复键清单。零耦合、可独立单测。
- `market_data_fetcher._fetch_market_prices` 在 upsert 前跑检测，将告警聚合成 JSON 写入 `quality_warnings`；`_finish_log` 与 `MarketDataFetchResult` 同步加字段，使告警可从返回值读取。
- alembic 迁移 `0008`：为 `data_fetch_log` 增加可空列 `quality_warnings`（非破坏）。
- 新增 `market-data` 规约的“重复交易日检测”requirement 及场景。

**不改**：upsert 的“后写覆盖先写”去重语义（规约强制）；provider 契约；计算层。本变更是 detect-only / WARN，不改变任何既有行为。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `market-data`: `DataFetchLog` ORM 模型新增 `quality_warnings` 可空列；市场价抓取工作流在 upsert 前检测同一批次内的重复交易日，并将告警写入 `quality_warnings`；新增“重复交易日检测”requirement。

## Impact

- **代码**：`packages/core/src/vela_core/models/data_fetch_log.py`（加字段）、新建 `packages/core/src/vela_core/data_quality.py`、`packages/core/src/vela_core/market_data_fetcher.py`（挂接 + `MarketDataFetchResult` / `_finish_log` 加字段）。
- **迁移**：`alembic/versions/20260709_0008_add_data_fetch_log_quality_warnings.py`（可空列，非破坏；当前 head 为 `0007`）。
- **测试**：新增 `packages/core/tests/test_data_quality.py`；扩展 `packages/core/tests/test_market_data_fetcher.py` 验证告警写入与返回值。
- **依赖**：无新增。
- **不改**：`market_price_upsert` 去重语义、`MarketDataProvider` 契约、`momentum_scoring` / `trend_filter` 等计算层。
- **未覆盖（留待后续 change）**：交易日缺口检测 `detect_trading_day_gaps` 依赖一个尚不存在的交易日历来源，作为独立 Phase 2 change；它将复用本次引入的 `quality_warnings` 落点。
