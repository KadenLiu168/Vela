## Why

`uv run vela fetch-market-data` 在本地拉取 6 只活跃 ETF 全量历史行情时会失败,报 `sqlite3.OperationalError: too many SQL variables`。SQLite 默认 `SQLITE_MAX_VARIABLE_NUMBER = 32_766` 是硬上限,本仓库当前调用方式下两个 SQL 路径都会撞上:

1. `_existing_market_price_keys` 中的 `tuple_(MarketPrice.etf_id, MarketPrice.trade_date).in_(keys)`:6 × 14 年 ≈ 21,000 键展开成 `IN (VALUES (?, ?), ...)` 子句 ≈ 42,000 个绑定参数。
2. `upsert_market_prices` 中的 `INSERT ... ON CONFLICT ... DO UPDATE`:21,000 行 × 8 列 ≈ 168,000 个绑定参数。SQLAlchemy 2.0 的 SQLite `insertmanyvalues` 优化只在 `session.execute(stmt, rows)` 形态下被激活,本仓库现在用的是 `insert(...).values(rows)` 烤进 statement 再 `session.execute(stmt)` 的单语句形态,该优化没有触发,所有值被内联成单条 SQL。

Phase 1 数据规模下两条路径都会爆,阻塞后续 `generate-signal` 与 `run-backtest` 的数据准备。

## What Changes

- `_existing_market_price_keys`:按 `BATCH_SIZE` 切片 `keys`,每片用一次 `tuple_(...).in_(...)` SELECT 取键,跨片取并集。
- `upsert_market_prices`:把 `insert(MarketPrice).values(rows)` + `session.execute(statement)` 改成 `insert(MarketPrice).on_conflict_do_update(...)` + `session.execute(statement, rows)`,让 SQLAlchemy 走 SQLite 的 `insertmanyvalues` 自动分批,不再手动切 INSERT。
- 保持 `upsert_market_prices` 的对外行为不变:签名、返回 `MarketPriceUpsertResult` 字段、on-conflict 冲突目标与列集合不变。
- 新增单元测试覆盖大批量 upsert(超过 18,000 行),断言不报 SQLite 参数上限错误、行数与 `rows_inserted` / `rows_updated` 计数正确。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `market-data`: 增加一条 requirement,明确"全量行情 fetch 必须在配置 ETF 池规模下成功落库,且不被 SQLite 单语句参数上限阻塞"。原有 ORM、日志、指标计算等 requirement 不变。

## Impact

- 修改:`packages/core/src/vela_core/src/vela_core/market_price_upsert.py`(单文件,`upsert_market_prices` 与 `_existing_market_price_keys` 两处)
- 新增测试:`packages/core/tests/test_market_price_upsert.py` 中针对大批量 upsert 的覆盖
- 公共 API 行为保持不变:`upsert_market_prices` 签名、返回 dataclass、`MarketPrice` 模型、`on_conflict_do_update` 的列集合与冲突目标都不变
- 不引入新依赖
- 不影响其他 ETF 池、CLI 命令、API 端点或 web 前端
