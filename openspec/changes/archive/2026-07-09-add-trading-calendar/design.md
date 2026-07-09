## Context

Phase 2 交易日缺口检测需要一个权威参照系——“哪些日子是 A 股交易日”。当前代码库没有任何交易日历。akshare 已是项目默认依赖，其 `tool_trade_date_hist_sina()` 接口返回 1990-12-19 起的全部 A 股交易日（pandas DataFrame，含 `trade_date` 列）。

项目已有可参照的同步模式：
- `etf_pool_sync.py`：`sync_etf_pool_to_db(session, pool) -> ETFPoolSyncResult`，frozen dataclass 计数 + select/add/setattr upsert。
- CLI `sync-etf-pool`：argparse subparser + `--database-url` + dispatch 包装函数（create engine/session + 调 core）。
- `market_price_upsert.py`：SQLite `insert.on_conflict_do_update` upsert 模式。

迁移当前 head 为 `0008`（Phase 1 的 `quality_warnings`）。

约束：
- 日历是全局数据，不是 per-symbol——不能复用 `BaseMarketDataProvider`（其契约是 per-symbol `get_etf_daily_prices`）。
- 保持 change 独立：纯数据基础设施，不含检测逻辑，不耦合 `DataFetchLog`。
- akshare 单源（joinquant 日历留待后续多源对比 change）。

## Goals / Non-Goals

**Goals:**
- `trading_calendar` 表（`trade_date` PK + `source` + 时间戳），与项目其他表风格一致。
- `sync_trading_calendar_to_db(session)` 同步函数，调 akshare `tool_trade_date_hist_sina`，upsert 全部交易日，返回 `TradingCalendarSyncResult`。
- CLI 命令 `vela sync-trading-calendar`（镜像 `sync-etf-pool`）。
- 非破坏 alembic 迁移 `0009`。

**Non-Goals:**
- 不做缺口检测 `detect_trading_day_gaps`（后续 `add-trading-day-gap-detection` change）。
- 不写 `DataFetchLog`（日历同步低频，保持 change 独立）。
- 不动 `MarketDataProvider` 契约、`market_data_fetcher`、计算层。
- 不做多源日历对比（joinquant 日历留待后续，需凭证）。
- 不在前端/API 展示。

## Decisions

1. 表结构 `trading_calendar(trade_date PK, source, created_at, updated_at)`。
   - Rationale：与 `etf_info`/`market_price` 风格一致；`source` 记录来源（akshare）便于未来多源对比；时间戳是项目惯例。
   - Alternative：单列 `trade_date PK`——最简，但缺 `source` 无法追溯来源，与项目风格不一致。

2. 同步函数 `sync_trading_calendar_to_db(session, *, source="akshare") -> TradingCalendarSyncResult` 镜像 `etf_pool_sync` 模式。
   - Rationale：项目既有同步模式，保持一致；frozen dataclass 计数可测试。
   - Alternative：复用 `market_data_fetcher._fetch_market_prices` + `DataFetchLog`——语义不同（日历不是 per-ETF market price），且耦合 fetch 日志基础设施。

3. upsert 用 SQLite `insert.on_conflict_do_update`（参照 `market_price_upsert`），冲突目标是 `trade_date` PK。
   - Rationale：历史交易日不变，upsert 幂等可重复跑；`on_conflict_do_update` 是项目既有模式。
   - Alternative：全量删表重建——破坏性，丢 `created_at`，且同步中途失败会丢数据，不可取。

4. 不写 `DataFetchLog`。
   - Rationale：日历同步低频（偶尔手动跑），`target_type` 语义是 market price fetch；保持 change 1 独立纯数据基础设施。`TradingCalendarSyncResult` 自带 `status`/计数提供可观测性。
   - Alternative：写 `DataFetchLog(target_type="trading_calendar")`——统一 fetch 日志，但耦合且超出最小范围。

5. akshare 调用直接 `import_module("akshare").tool_trade_date_hist_sina()`，不走 `BaseMarketDataProvider`。
   - Rationale：日历是全局数据，不是 per-symbol；`BaseMarketDataProvider` 契约是 per-symbol `get_etf_daily_prices`，不适合。直接调 akshare 函数最简单，且与 provider 契约解耦。
   - Alternative：扩展 provider 契约加 `get_trading_calendar`——契约膨胀，过度设计。

6. CLI 命令 `sync-trading-calendar` 镜像 `sync-etf-pool`（argparse subparser + `--database-url` + dispatch 包装函数）。
   - Rationale：项目既有 CLI 同步命令模式，保持一致，降低学习成本。

## Risks / Trade-offs

- [akshare `tool_trade_date_hist_sina` 返回范围到“当前”] → 接口持续更新；同步是幂等 upsert，定期跑即可覆盖新交易日。需文档说明“定期同步以覆盖新交易日”。
- [akshare 接口返回格式变化或失效] → 同步函数解析失败时返回 `failed` status + error，不崩溃；测试用 fake akshare module 覆盖正常/失败路径。
- [单源 akshare，无交叉验证] → Phase 1 评审指出 akshare 是单一后端；日历同样单源。留待后续 joinquant 日历多源对比 change。
- [`trading_calendar` 表只增不改] → 历史交易日不变，无需清理；未来若 akshare 修正历史（极罕见），upsert 会覆盖。

## Migration Plan

- 迁移 `20260709_0009_create_trading_calendar.py`：`CREATE TABLE trading_calendar`（`trade_date` PK, `source`, `created_at`, `updated_at`）。
- 回滚：`DROP TABLE trading_calendar`（新表无外部数据依赖）。
- 验证：`initialize_database` 建表路径与 `alembic upgrade head` 迁移路径都需覆盖新表（`test_sqlite_migration_head_matches_orm_metadata` 会强制 migration head 与 ORM metadata 一致）。

## Open Questions

- 是否需要 joinquant 日历作为第二源对比？→ 留待后续 change（需凭证，且 akshare 单源已足够 Phase 2 缺口检测）。
- 同步频率？→ 手动/定期 CLI，不自动化（个人研究系统）。
