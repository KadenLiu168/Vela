## Context

当前 `_get_market_data_status()` 用一条全局聚合查询获取所有 ETF 的 MIN/MAX trade_date，然后单独查 `etf_info` 获取已覆盖 ETF 的列表。这只给出了整体覆盖范围，无法区分每只 ETF 的数据起点。

Vela 的 ETF 池包含不同市场的基金（A 股、美股、港股、商品、债券），它们的数据起始日期差异很大 — 比如沪深300ETF 从 2012 年就有数据，而科创50ETF 从 2020 年才开始交易。回测时如果不知道这个差异，选了一个某些 ETF 还没出生的日期，策略在那些日期会拿到不完整的数据。

## Goals / Non-Goals

**Goals:**
- Dashboard API 返回的每只 ETF 条目包含该 ETF 在 `market_price` 表中的最早 `trade_date`
- 前端单列展示 ETF，每行右侧显示最早日期，方便用户一目了然地判断回测起始时间

**Non-Goals:**
- 不修改全局 coverage timeline — 保留所有 ETF 的并集范围
- 不修改 `market_data_fetcher.py` 的数据获取逻辑
- 不增加新的 API endpoint — 改动仅在 `/api/dashboard` 响应中

## Decisions

### Decision 1: 合并查询而非新增独立查询

将 per-ETF `MIN(trade_date)` 计算合并到获取 `etf_list` 的单条查询中，使用 JOIN + GROUP BY 替代当前的子查询 IN 模式。

**替代方案**: 先查 `etf_list`，再对每个 ETF 单独查 `MIN(trade_date)`。  
**选择理由**: 单条 JOIN + GROUP BY 查询只需一次数据库往返，SQLite 对此类查询有良好优化（复合索引 `ix_market_price_etf_trade_date` 覆盖 `(etf_id, trade_date)`）。

**变更前查询**:
```python
# 子查询方式 — 只取 ETF 元数据
select(ETFInfo.exchange, ETFInfo.symbol, ETFInfo.name, ETFInfo.category)
.where(ETFInfo.id.in_(select(MarketPrice.etf_id).distinct()))
```

**变更后查询**:
```python
# JOIN + GROUP BY — 同时获取元数据和最早日期
select(
    ETFInfo.exchange, ETFInfo.symbol, ETFInfo.name, ETFInfo.category,
    func.min(MarketPrice.trade_date).label("earliest_trade_date"),
).join(MarketPrice, MarketPrice.etf_id == ETFInfo.id).group_by(
    ETFInfo.id, ETFInfo.exchange, ETFInfo.symbol, ETFInfo.name, ETFInfo.category
)
```

INNER JOIN 自动过滤无 market_price 行的 ETF，行为与原子查询一致。

### Decision 2: 全局 earliest/latest 不变

全局 `earliest_trade_date` 和 `latest_trade_date` 查询保持原样（`func.min(trade_date)` 无 GROUP BY）。coverage timeline 仍然是所有 ETF 的并集范围，提供总览参考。

### Decision 3: 新增字段而非拆分结构

在 `EtfBrief` 上新增 `earliest_trade_date: date | None`，不改动 `DashboardMarketDataStatus` 的顶层结构。全局日期和 per-ETF 日期共存于同一个响应中，前端可自由组合使用。

### Decision 4: CSS 单列 + 行尾日期

`.etf-row-list` 从 2-column grid 改为单列。每行内部用 flexbox 布局，日期通过 `margin-left: auto` 推到右侧。日期文字使用缩小的 monospace 字体（`var(--font-berkeley-mono)`），颜色为 `var(--color-fog)`，与现有代码风格一致。

## Risks / Trade-offs

- **ETF 数量增长后列表变长**: 当前只有 9 只 ETF，单列布局完全可接受。如果未来 ETF 池扩展到 30+，可能需要考虑折叠或分组。→ 届时可重新评估，当前不做过度设计。
- **`earliest_trade_date` 为 null**: 理论上 INNER JOIN 保证每组至少有一行，MIN 不会返回 null。但 SQLAlchemy 类型推断无法静态证明这一点，因此类型标注为 `date | None`。→ 前端用 `string | null` 对应，渲染时 null 显示 `—`。

## Migration Plan

无需数据迁移。改动仅涉及查询逻辑和 UI 布局。部署后端后刷新 dashboard 即可看到新字段。前端与后端独立部署，新旧版本兼容 — 前端不识别新字段时仅忽略显示，不影响现有功能。
