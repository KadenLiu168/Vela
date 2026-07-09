## Context

Vela 的数据层目前只做逐行级校验（`base_market_data_provider._normalize_rows`：缺值、非正价、OHLC 一致性、成交量），缺少批次级校验。`market_price_upsert._deduplicate_market_prices`（`packages/core/src/vela_core/market_price_upsert.py:60-66`）对同一 `(etf_id, trade_date)` 用字典赋值“后者赢”去重——这是 `market-data` 规约强制的行为（spec 152-158 行）。结果是：重复行被静默折叠，写入值可能与真实值不符，且系统从不报错。

`DataFetchLog`（`models/data_fetch_log.py`）目前只有 `error_message` 一个文本字段承载硬失败信息，没有“数据质量软信号”的落点。fetch 工作流（`market_data_fetcher._fetch_market_prices`）在 upsert 前恰好持有整批 `market_prices` 列表（line ~121-145），是做批次级检测的天然边界。

约束：
- 去重语义由规约强制，不可改。
- 计算层（`momentum_scoring` / `market_price_moving_average` / `trend_filter`）是纯函数、不持 Session，新检测逻辑应遵循同一模式。
- provider 是 `Protocol`，契约不应膨胀。
- 数据库迁移走 alembic（当前 head `0007`），变更走 OpenSpec。

## Goals / Non-Goals

**Goals:**
- 引入 `quality_warnings` 软信号落点（nullable `Text`，存 JSON），与硬失败的 `error_message` 分离。
- 提供纯函数 `detect_duplicate_trade_dates(prices)`，零耦合、可独立单测。
- 在 fetch 路径 upsert 前挂接检测，告警可从 `DataFetchLog` 与 `MarketDataFetchResult` 双向读取。
- 非破坏的 alembic 迁移。

**Non-Goals:**
- 不改 upsert 的“后写覆盖先写”去重语义（规约强制）。
- 不做交易日缺口检测 `detect_trading_day_gaps`——它依赖一个尚不存在的交易日历来源，作为独立 Phase 2 change。
- 不引入 strict / 硬失败模式——本阶段纯 WARN。
- 不动 provider 契约与计算层。
- 不在前端 / API 暴露告警——Phase 1 后端 only。

## Decisions

1. `quality_warnings` 用 nullable `Text` 存 JSON，而非独立表或原生 JSON 类型。
   - Rationale：SQLite 无原生 JSON 类型；`Text` + JSON 字符串最简单；一个 fetch 对应一行 log，告警天然 1:1 挂在 log 上，无需独立表。
   - Alternative：独立 `data_quality_warning` 表（1:N）——Phase 1 告警量小，过度设计；JSON 数组足够且查询路径简单。

2. `detect_duplicate_trade_dates` 为纯函数，入参 `Sequence[MarketPrice]`，不持 Session、不改输入。
   - Rationale：契合项目“计算/检测层纯函数”模式（参照 `momentum_scoring._momentum_score_from_prices`、`market_price_moving_average._moving_average_from_prices`）；可独立单测，不依赖 DB。
   - Alternative：在 `upsert_market_prices` 内部检测——会污染 upsert 的单一职责，且 upsert 已有 chunking 逻辑。

3. 检测在 `market_data_fetcher._fetch_market_prices` 内、upsert 前挂接（当前 line ~142 之前），而非在 provider 或 upsert。
   - Rationale：fetcher 是“一个 fetch 批次”的边界，恰好拥有整批 `market_prices` 列表；provider 逐 symbol 返回，看不到全批；upsert 不应承担检测职责。
   - Alternative：在 provider 检测——provider 逐 symbol，且 provider 契约不应膨胀。

4. detect-only / WARN，绝不改 last-write-wins。
   - Rationale：`market-data` 规约（152-158 行）强制 batch 内重复键用最后值；改语义会破坏规约并影响既有 upsert 测试。告警是可观测软信号。

5. `quality_warnings` JSON 信封格式：`{"duplicate_trade_dates": [{"etf_id": <int>, "trade_date": "<ISO>", "count": <int>}, ...]}`。
   - Rationale：结构化、可扩展（Phase 2 加 `"trading_day_gaps"` 顶层键即可），又足够简单。
   - Alternative：自由文本——不可解析、难扩展、难测试。

6. 迁移 `0008` 仅加可空列，无数据回填。
   - Rationale：既有 log 行无告警，`null` 即“未检测 / 无告警”，语义自洽；SQLite 支持可空列加法，非破坏。

## Risks / Trade-offs

- [告警是尽力而为软信号，fetch 中途失败时 `quality_warnings` 可能未写] → 与 `error_message` 分离；失败时 `status=failed/partial` 仍可区分；告警缺失不代表数据干净，需在文档说明“null = 未检测或无告警”。
- [`quality_warnings` JSON schema 无 DB 级约束] → 由纯函数 + 测试保证形状；未来若需强约束再迁移。
- [重复检测对正常 AkShare 数据几乎总为空（同 symbol 一日一行）] → 这是预期；检测是安全网，针对源异常或未来多源合并场景；成本极低（一次字典计数）。
- [Phase 2 缺口检测会复用同字段，schema 需前向兼容] → 信封用顶层键分组，Phase 2 加键不破坏 Phase 1 消费者。

## Migration Plan

- 迁移 `20260709_0008_add_data_fetch_log_quality_warnings.py`：`ALTER TABLE data_fetch_log ADD COLUMN quality_warnings TEXT`（SQLite 支持可空列加法，非破坏）。
- 回滚：无需特殊处理（可空列，旧代码忽略该字段即可）；如需清理可后续删列迁移。
- 验证：`initialize_database` 建表路径与 `alembic upgrade` 迁移路径都需覆盖新列（项目存在这两条数据库初始化路径，需各自测试）。

## Open Questions

- `quality_warnings` 是否需要在 dashboard / API 暴露？→ Phase 1 后端 only，前端展示留待后续 change。
- 告警阈值（如重复数超过 N 才告警）？→ Phase 1 不设阈值，有重复即告警，保持简单。
