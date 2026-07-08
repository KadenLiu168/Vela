## Context

Vela 当前在 `packages/core/src/vela_core/strategy_signal_generation.py` 的 `generate_strategy_signal` 中，对 `Session` 强耦合：函数接受 `session` 形参并将其透传给 `apply_trend_filter`、`calculate_momentum_score`、`_list_active_etfs`、`_to_generated_position`、`persist_strategy_signal`。其中两个读路径存在可消除的 N+1：

1. **per-ETF 重复查询**：每个 active ETF 都跑 2 次 `MarketPrice`（`apply_trend_filter` 内部的当前价 + 均线窗口），通过 trend 的再 +1 次（动量窗口）。设 N=11 ETF，单次信号对 `MarketPrice` 的读数 ≈ 1 + 2N + M。
2. **行集层层包含**：trend 内部的 `LIMIT window` 与 momentum 的 `LIMIT long_window+1` 高度重叠（min(120, 127) = 120 行重复），且 `as_of_date` 单点价位被读 2 次。

`generate_historical_strategy_signals` 把每次 rebalance 日当作独立调用，导致 5 年 weekly 回测对 `MarketPrice` 触发 ~9k 次查询。当前数据层没有「按 ETF 列表 × 时间段批量取数」的公开 API——唯一的多 ETF 批量读 `strategy_equity_curve._load_prices_by_key` 是私有、依赖 holding snapshots 的局部辅助。

`apply_trend_filter` / `calculate_momentum_score` / `calculate_market_price_moving_average` 三个函数都把「DB 取数」与「纯计算」混在一起，单测不得不依赖 DB session。

## Goals / Non-Goals

**Goals:**
- 在 `MarketPrice` 上新增「一次 IN 拉所有 ETF × 区间」的一阶公开接口（`load_price_panel`），作为多 ETF × 时间段批量读取的唯一推荐基元。
- 把信号生成的「DB 取数」与「纯计算」物理拆开，使纯计算部分可在不依赖数据库的情况下被测试和复用。
- 把 `generate_strategy_signal` 改成纯函数：`session` 不再入参；元数据（active_etfs / defense_lookup）与价格序列（price_panel）由调用方注入。
- 让回测（per rebalance × per ETF 的循环）复用同一份 panel，把整段回测对 `MarketPrice` 的查询降到 1 次。
- 保持回测业务语义 byte-equivalent：相同输入下的 `StrategySignal` 行必须与改前一致。

**Non-Goals:**
- 不引入进程内 / 跨进程缓存层（任务 3 留待后续 change）。
- 不修改 `MarketPrice` 表 schema、不新增索引、不修改 `StrategyConfig` YAML schema。
- 不修改回测净值、持仓、换手、年化等下游计算路径。
- 不修改 `MarketDataProvider` 写路径（行情拉取 / upsert）。
- 不引入 pandas 依赖到 hot path 的纯计算函数（保持现有 `Decimal` / `list` 风格）。

## Decisions

### 1. 新增 `load_price_panel` 作为唯一推荐的多 ETF × 时间段读基元

位置：`packages/core/src/vela_core/market_price_query.py`。

```python
def load_price_panel(
    session: Session,
    *,
    etf_ids: Sequence[int],
    start_date: date | None = None,
    end_date: date,
    columns: Sequence[str] = ("trade_date", "strategy_price"),
) -> dict[int, list[MarketPrice]]:
    """一次 IN 查询，按 etf_id 分组返回升序价格序列。

    复用 ix_market_price_etf_trade_date 复合索引。
    调用方负责 panel 的复用与生命周期。
    """
```

- 默认列只取 `trade_date` 与 `strategy_price`（即 `adjusted_close` 或 `close_price`，复用 `MarketPrice.strategy_price` 派生属性）。
- `start_date=None` 时由调用方根据窗口大小自行回推（不强制在 DAO 层硬编码）。
- 不暴露 `yield_per` / 流式接口——当前数据规模（11 ETF × 5y ≈ 14k 行）远低于内存阈值；引入流式接口会增加调用方复杂度、收益微薄。
- 返回结构按 `etf_id` 分组的 `list[MarketPrice]` 升序，与现有 `momentum_scoring` / `market_price_moving_average` 的消费模式一致，避免 DataFrame 化带来的 pandas 耦合。

**为什么不直接抽 `MarketPriceRepository` 类？** 当前 `vela_core` 没有 Repository 抽象层（`Explore` 报告确认），DAO 全部以函数形式存在。保持风格一致、不引入新的抽象层级。

### 2. 三段式拆分「DB 取数 / 纯计算 / 编排」

每个被拆的函数保留原函数名为「DB 取数入口」并标 deprecated 注释；新增下划线私有纯计算函数供 `generate_strategy_signal` 内部调用：

| 原函数 | DB 取数入口（保留） | 新增纯计算函数（私有 / 公开） |
|---|---|---|
| `apply_trend_filter(session, *, etf_id, as_of_date, config)` | 委派到 `_trend_filter_from_panel(panel_entry, config)` | `_trend_filter_from_panel(prices: list[MarketPrice], config) -> TrendFilterResult`（module-public 给上层复用，单测直接喂 list） |
| `calculate_momentum_score(session, *, etf_id, as_of_date, config)` | 委派到 `_momentum_score_from_panel(panel_entry, config)` | `_momentum_score_from_panel(prices: list[MarketPrice], config) -> MomentumScore` |
| `calculate_market_price_moving_average(session, *, etf_id, as_of_date, window)` | 委派到 `_moving_average_from_prices(prices, window)` | `_moving_average_from_prices(prices: list[MarketPrice], window) -> MarketPriceMovingAverage` |

**为什么不彻底删除旧函数？** 它们仍然是 CLI / API 实时路径的便捷入口（单 ETF 单次调用场景下，调用 `load_price_panel` 然后委派到纯计算反而绕一层）。保留旧函数 + 委派实现 = 兼容 + 收敛。

**为什么不直接全部函数化 `Decimal` 列表？** 现有代码风格是 `list[MarketPrice]`（保留 ORM 语义），且 `MarketPrice.strategy_price` 是已封装的派生属性。强转 `Decimal` 列表会让纯计算函数失去对 `trade_date` 的直接访问（momentum 要校验 `prices[0].trade_date == as_of_date`）。

### 3. `generate_strategy_signal` 改为纯函数 + 依赖注入

新签名：

```python
def generate_strategy_signal(
    *,
    signal_date: date,
    config: StrategyConfig,
    price_panel: dict[int, list[MarketPrice]],
    active_etfs: list[ETFInfo],
    defense_lookup: dict[tuple[str, str], ETFInfo],
    generated_at: datetime | None = None,
    persist: Callable[[GenerateStrategySignalResult], None] | None = None,
) -> GenerateStrategySignalResult:
```

关键设计点：
- `session` 完全消失；调用方自己持有 `session` 并在调用前后管理事务。
- `price_panel` 是「调用方承诺已注入好」的入参；纯函数内部不再发起任何 `MarketPrice` 查询。
- `active_etfs` 由调用方提前查好并注入，消除每个 rebalance 日都重查 `etf_info` 的浪费。
- `defense_lookup` 是 `(exchange, symbol) -> ETFInfo` 字典，调用方从 `active_etfs` 一次性构造；`_to_generated_position` 走 dict 命中不再查 DB。
- `persist` 回调让「纯计算 / 持久化」解耦：CLI / API / backtest 可以共用同一个纯函数，仅在编排层决定是否落库。默认行为 = 不持久化，调用方必须显式传 `persist` 才能写库。

**为什么把 persist 设计成回调而非「编排层包一层」？** 单测场景下完全不写库；CLI 路径希望"生成 + 落库"原子化；backtest 路径希望"批量生成 + 批量落库"。回调统一这三种意图。

### 4. 回测入口一次性 panel 加载

`run_backtest` 改造：

```python
trading_dates = _load_trading_dates(...)
rebalance_dates = generate_rebalance_dates(trading_dates, frequency=config.rebalance.frequency)
all_etfs = list_active_etfs(session)
defense_lookup = {(e.exchange, e.symbol): e for e in all_etfs}

# 一次 panel 覆盖整个回测区间 + 回推窗口
panel_window_start = rebalance_dates[0] - timedelta(
    days=max(config.momentum.long_window_days, config.trend_filter.moving_average_days) + 5
)
price_panel = load_price_panel(
    session,
    etf_ids=[e.id for e in all_etfs],
    start_date=panel_window_start,
    end_date=rebalance_dates[-1],
)

signal_results = generate_historical_strategy_signals(
    rebalance_dates=rebalance_dates,
    config=config,
    price_panel=price_panel,
    active_etfs=all_etfs,
    defense_lookup=defense_lookup,
    persist=lambda result: persist_strategy_signal(session, ...),
)
```

**为什么不在 `generate_historical_strategy_signals` 内部再调一次 `load_price_panel`？** 该函数仍是纯函数（不接 `session`），把 panel 加载下沉到调用方，让 backtest 与 CLI 各自控制 panel 的边界。

### 5. 行集冗余消除策略

- **truncate 到 `max(long_window, ma_window) + 1`**：调用方注入 panel 时回推足够的历史。交易日→日历日换算用 `max_window * 2 + 10` 日历日（~252 交易日/365 日历日 ≈ 0.69 比率，`* 2` 给节假日/停牌留充足余量），确保第一个 rebalance 日有足够 trading-day 历史满足 trend + momentum 窗口。
- **纯计算内部各自 slice**：trend 在 `prices[-window:]` 取 MA，momentum 在 `prices[-(long_window+1):]` 取 return；不存在跨函数重复 SQL。
- **as_of_date 单点价位不重复**：从 `prices[-1]`（升序最后一行 = 最新一日）直接取，与 MA 的 `prices[-window:].mean()` 共用同一份内存序列。

### 6. CLI / API 实时路径改造

CLI `vela signal generate` 与 API `POST /api/strategy-signals/generate` 改为：

```
load_active_etfs(session) → active_etfs
build_defense_lookup(active_etfs) → defense_lookup
load_price_panel(session, etf_ids, end_date=signal_date) → price_panel
generate_strategy_signal(...) → result
persist_strategy_signal(session, ...) → DB
```

单次信号对 `MarketPrice` 仅 1 次查询。

### 7. 回归验证策略

- 纯函数单测：覆盖 trend / momentum / 全 signal 路径，喂入 fixture `list[MarketPrice]`，断言 `TrendFilterResult` / `MomentumScore` / `GenerateStrategySignalResult` 字段。
- 集成回归：在 SQLite fixture 上跑一次 5y weekly 回测 + 一次实时信号生成，比对改前 / 改后产出的 `StrategySignal` 行（`signal_date`、`result`、`positions[].etf_id / rank / score / target_weight`）**byte-equivalent**。
- SQL 调用计数断言（性能验收而非功能验收）：在测试中 monkey-patch `session.scalar` / `session.scalars` 计数，断言单次回测对 `MarketPrice` 表的查询 ≤ 1 次。

## Risks / Trade-offs

- **旧函数（`apply_trend_filter` / `calculate_momentum_score` 等带 session 入参）仍保留为兼容入口** → 风险：未来调用方可能继续用旧入口，回退到 N+1 模式。**Mitigation**：在旧函数 docstring 加 deprecation 注释；并在单测中加一条「旧入口 N+1 计数上限」的回归断言，避免悄悄退化。
- **`price_panel` 是大对象，跨调用复用靠调用方负责** → 风险：backtest 路径忘记复用、每次 rebalance 重新 load。**Mitigation**：`run_backtest` 在循环外加载一次；tasks.md 的 acceptance criteria 明确 SQL 计数上限。
- **回测结果必须 byte-equivalent** → 风险：纯计算函数从「按 `LIMIT long_window+1`」改为「按升序 `prices[:long_window+1]`」可能在边界条件（如交易日历不连续）下结果略有差异。**Mitigation**：在 panel 加载时确保升序 + 包含 `as_of_date` 行；并在 PR 描述里贴出 byte-equivalent 比对日志。
- **`MarketPrice.strategy_price` 是 ORM 派生属性** → 风险：纯计算函数依赖 ORM 实体而非 `Decimal` 列表，绑定较紧。**Mitigation**：保持现有风格一致；不引入 pandas；如未来要 DataFrame 化是另一个 change。
- **public API 签名变更（移除 `session`）** → BREAKING。**Mitigation**：本次 PR 同步改造 CLI / API / 单测三个调用方，没有外部消费者（Phase 1 自用系统）。
- **panel 大小与内存** → 11 ETF × 5y ≈ 14k 行 ≈ 几 MB，可忽略；若 ETF 池扩到 100+ × 5y 约 130k 行 / 几百 MB，仍可接受。**Mitigation**：design 文档明确"当前规模无问题"，未来若突破再上 `yield_per` 流式接口。

## Migration Plan

- 单 PR 完成：任务 1（纯函数化 + panel）+ 任务 2（回测单次加载）一起上，避免中间状态。
- 步骤：
  1. 新增 `market_price_query.load_price_panel` + 单测。
  2. 拆分三个纯计算函数 + 旧入口委派。
  3. 改造 `generate_strategy_signal` / `generate_historical_strategy_signals` 为纯函数。
  4. 改造 CLI / API 实时路径。
  5. 改造 `run_backtest` 入口一次性加载。
  6. 改造现有单测为纯函数测试；新增 panel 接口单测 + byte-equivalent 集成回归 + SQL 计数断言。
  7. 跑全量回归：`uv run pytest`、CLI `vela backtest run` 端到端、人工目检仪表盘净值曲线与改前一致。
- 回滚：单 PR，单 commit revert 即回滚全部变更。

## Open Questions

- `apply_trend_filter` / `calculate_momentum_score` 是否要正式标 `@deprecated`（让 ruff / mypy 报 warning）？倾向：暂不加 `@warnings.warn`，只在 docstring 写明；任务 3 之后再统一清理。
- byte-equivalent 的范围：本次只比对 `StrategySignal` 行；不动 `BacktestEquityCurve`（由 `calculate_strategy_equity_curve` 单独产生，其加载路径已经批量）。需在 PR 描述里说明。
- panel 加载是否要支持「按 (etf_id, trade_date) 起点裁剪」以避免拉全部历史？当前 SQLite 全量 14k 行直接拉，没有裁剪必要；若未来 ETF 池扩到数千只再讨论。