## Context

`packages/core/src/vela_core/market_price_upsert.py` 中的 `upsert_market_prices(session, market_prices)` 跑两条 SQL:

1. `SELECT etf_id, trade_date FROM market_price WHERE (etf_id, trade_date) IN (...)`:落库前查已有键,用来算 `rows_inserted` / `rows_updated`。
2. `INSERT INTO market_price ... ON CONFLICT (etf_id, trade_date) DO UPDATE`:实际落库。

`vela fetch-market-data` 拉 6 只 ETF 全量 ≈ 21,000 行,在本地 SQLite 上都炸:

- 第 1 条:21,000 键 × 2 = 42,000 绑定参数,展开成 `IN (VALUES (?, ?), ...)` 后超过 SQLite 默认 `SQLITE_MAX_VARIABLE_NUMBER = 32_766`。SQLAlchemy 2.0.51 的 `expanding=True` 自动分批对**单列** IN 起作用,但对 `tuple_(...).in_(list_of_tuples)` **不展开**,本仓库这条路径不会被分批。
- 第 2 条:21,000 行 × 8 列 = 168,000 绑定参数。SQLAlchemy 2.0.51 的 SQLite `insertmanyvalues` 自动分批**只在 `session.execute(stmt, rows)` 形态下激活**(rows 在 execute 时传入);本仓库当前是 `insert(...).values(rows)` 烤进 statement 再 `execute(stmt)`,走单语句编译,所有 VALUES 内联成一条 SQL,该优化不触发。

调用方只有 `market_data_fetcher.fetch_full_market_prices` / `fetch_incremental_market_prices`,都通过 `upsert_market_prices` 提交一批 `MarketPrice`。两条 SQL 都要在本地 SQLite 上能跑 6 × 14 年规模的数据。

## Goals / Non-Goals

**Goals:**

- `_existing_market_price_keys` 在键数远超 SQLite 单语句参数上限时仍能完整返回命中集合。
- `upsert_market_prices` 的 INSERT 路径在行数远超 SQLite 单语句参数上限时仍能成功落库。
- 保持 `upsert_market_prices` 的对外行为:返回 `rows_inserted` / `rows_updated` 计数与"一次 SELECT + 一次 INSERT"语义一致。
- 为大批量 upsert 增加单元测试,锁住回归。

**Non-Goals:**

- 更换本地数据库(继续使用 SQLite 作为 Phase 1 开发库)。
- 改 `MarketPrice` 模型、列、`UniqueConstraint`、索引。
- 改 `fetch-market-data` CLI、provider 实现、fetch 流程或日志。
- 引入新依赖或调整 `pyproject.toml`。

## Decisions

1. `_existing_market_price_keys` 内显式按批调 `session.execute`,每批键数固定为 `BATCH_SIZE = 16_000`,跨批取并集。

   Rationale: 每个键 `(etf_id, trade_date)` 展开成 2 个绑定参数,`16_000 × 2 = 32_000` 略低于 SQLite 默认 `SQLITE_MAX_VARIABLE_NUMBER = 32_766`,留几百参数余量;Phase 1 6 × 14 年规模只需 2 个 batch,几乎无额外往返。整数常数易读易测。

   Alternative considered: 让 `BATCH_SIZE` 派生自"每键列数 × N < 32766"。`_existing_market_price_keys` 当前只有 `(etf_id, trade_date)` 一种键,显式 `BATCH_SIZE = 16_000` 已足够安全,暂不引入派生逻辑。

2. `upsert_market_prices` 把 INSERT 改为 `session.execute(statement, rows)` 形态(不再用 `insert(...).values(rows)` 烤进 statement),由 SQLAlchemy 自动走 SQLite `insertmanyvalues` 分批。

   Rationale: 一行调用风格变化,激活库内建优化,不需要在用户代码里手动切 INSERT。SQLAlchemy 2.0 在 SQLite 上对 `insertmanyvalues` 的支持是文档化的稳定行为,不比手写分批差。`on_conflict_do_update` + `excluded.*` 引用在 executemany 路径下也工作正常(已实测)。

   Alternative considered: 在 `upsert_market_prices` 里手动切 INSERT。和 SELECT 那条手切对齐,逻辑一致,但要多写 5–10 行,且 INSERT 与 `on_conflict_do_update` 组合上手动切容易写错(`excluded.*` 引用要重新构造、循环里要重建 statement 等)。`insertmanyvalues` 已经在库内做对,信任库。

3. 复用现有的 `select(MarketPrice.etf_id, MarketPrice.trade_date).where(tuple_(...).in_(keys))` 构造,只在 `_existing_market_price_keys` 外层包一个 batch loop,`set` 取并集,不动 SQL 表达式。

   Rationale: 维持"dedup → 查已有键 → 写库"这条单一链路,只把原来一次 SELECT 换成多次 SELECT。`_market_price_values`、dedup、INSERT 的 `on_conflict_do_update` 列集合不动,回归面最小。

4. `BATCH_SIZE` 定义为模块级 `BATCH_SIZE: int = 16_000`,不加配置项。

   Rationale: 这是数据库硬限制的派生态,不属于用户可调参数。Phase 1 不引入新的 YAML/环境变量配置面。

5. 测试在 `packages/core/tests/test_market_price_upsert.py` 中追加,沿用现有 `_create_session_factory` / `_add_etf` / `_market_price` 风格,构造至少 18,000 行的 upsert(超过本机 SQLite 单语句参数上限的 ~36,000 个),断言两条 SQL 路径都不报 `too many SQL variables`、行数正确、upsert 行为仍按 `(etf_id, trade_date)` 工作。

   Rationale: 直接回归这次失败的根因;用内存 SQLite 避免污染本地 `vela.db`。

## Risks / Trade-offs

- 多个小 SELECT 比一个 SELECT 多一次往返,极端情况 21,000 键切 2 批,体感无影响 → Mitigation: 用 batch 数 ≤ 2 的设计,BATCH_SIZE 偏大。以后扩展到几十只 ETF × 几十年日线时再调。
- INSERT 改用 `session.execute(stmt, rows)` 后,SQL 编译路径与原代码不同,出错信息形态可能略有变化 → Mitigation: 测试覆盖完整 upsert 流程,异常信息仍由 SQLAlchemy 统一包装。
- 批与批之间如果进程异常退出,已有行会保留,未处理的键丢在内存里 → 与现状一致(失败时整次 fetch 也会被 `DataFetchLog` 标记为 `failed`)。Mitigation: 真正"全有或全无"语义超出本次 scope。
- `BATCH_SIZE` 是按 `_existing_market_price_keys` 当前键列数(2)硬算的,以后键的列数变化必须回看 → Mitigation: 在常量旁加注释说明"按当前 2 列键取,加列后需重新评估"。

## Migration Plan

1. 修改 `packages/core/src/vela_core/src/vela_core/market_price_upsert.py`:
   - `_existing_market_price_keys` 按 `BATCH_SIZE` 切片循环执行 SELECT,结果合并到 `set`。
   - `upsert_market_prices` 把 `insert(...).values(rows)` + `session.execute(stmt)` 改成 `insert(...).on_conflict_do_update(...)` + `session.execute(stmt, rows)`。
2. 扩充 `packages/core/tests/test_market_price_upsert.py`,覆盖大批量 upsert。
3. 运行 `uv run pytest packages/core/tests/test_market_price_upsert.py` 与 `uv run ruff check .` / `uv run ruff format --check .`。
4. 手动验证:在干净 `vela.db` 上跑 `uv run vela sync-etf-pool && uv run vela fetch-market-data`,确认不再报 `too many SQL variables`,并打印出预期的 `rows_inserted` / `rows_updated`。

回滚:还原 `market_price_upsert.py` 单文件即可,没有数据迁移、没有 schema 变更。

## Open Questions

- None.
