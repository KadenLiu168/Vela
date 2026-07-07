## Context

当前 Market Data 卡片通过一次聚合查询获取统计数据（price_rows、covered_etfs、earliest/latest trade_date），只返回了 `covered_etfs` 这个数字。用户看不到具体是哪几个 ETF 有行情数据。

后端 `etf_info` 表已在数据同步时写入完整的 ETF 元数据（exchange、symbol、name、category 等），`MarketPrice` 表记录了每条行情数据且通过 `etf_id` 外键关联 `etf_info`——数据链路完整，只缺一层查询透传。

## Goals / Non-Goals

**Goals:**
- Dashboard API 响应中返回有行情数据的 ETF 列表（exchange、symbol、name）
- Market Data 卡片以 badge 形式展示该列表
- 所有 mock 数据和测试同步覆盖新字段

**Non-Goals:**
- 不从 `config/etf_pool.yaml` 取 ETF 列表（数据来源为 MarketPrice → etf_info DB JOIN）
- 不修改 ETF 元数据本身的同步逻辑
- 不分页、不搜索、不筛选（≤9 条，无需分页机制）

## Decisions

### 1. 数据来源：DB JOIN，而非配置池

| 方案 | 评估 |
|---|---|
| **从 `config/etf_pool.yaml` 取** | 所有配置中的 ETF，不管有没有行情数据都被列出 |
| **从 DB JOIN `MarketPrice` → `etf_info` 取 ✅** | 只返回真正有行情记录的 ETF，与 `covered_etfs` 统计口径一致 |

选择后者，与现有 `count(distinct MarketPrice.etf_id)` 逻辑同源，用户看到的就是实际可用的数据。

### 2. 后端实现：单独查询，不改造已有聚合 QUERY

`_get_market_data_status()` 当前是一个聚合行查询（`count` + `min` + `max`），改造为 JOIN 返回行集不划算。改为新增一条独立查询：

```python
etf_rows = session.execute(
    select(ETFInfo.exchange, ETFInfo.symbol, ETFInfo.name)
    .where(ETFInfo.id.in_(
        select(MarketPrice.etf_id).distinct()
    ))
    .order_by(ETFInfo.exchange, ETFInfo.symbol)
).all()
```

两者各自保持简单，总开销为两次轻量查询。

### 3. 数据结构

**Python (dataclass):**
```python
@dataclass(frozen=True)
class EtfBrief:
    exchange: str
    symbol: str
    name: str

# DashboardMarketDataStatus 新增字段
etf_list: tuple[EtfBrief, ...] = ()
```

**TypeScript:**
```typescript
export type EtfBrief = {
  exchange: string;
  symbol: string;
  name: string;
};

// DashboardMarketDataStatus 新增字段
etf_list: EtfBrief[];
```

### 4. 前端 UI 布局

```
┌──────────────────────────────────┐
│ Market → Market data             │
│                                  │
│ Price rows      46,020 rows      │
│ Covered ETFs        9 ETFs       │
│                                  │
│ ┌────────┐ ┌────────┐ ┌──────┐  │
│ │510300 ·│ │159915 ·│ │512100│  │
│ │沪深300ETF│ │创业板ETF│ │中证… │  │
│ └────────┘ └────────┘ └──────┘  │
│ ┌────────┐ ┌────────┐ ┌──────┐  │
│ │513500 ·│ │518880 ·│ │588000│  │
│ │标普500ETF│ │黄金ETF │ │科创… │  │
│ └────────┘ └────────┘ └──────┘  │
│ ┌────────┐ ┌────────┐ ┌──────┐  │
│ │513180 ·│ │159941 ·│ │511010│  │
│ │恒生科技ETF│ │纳指ETF │ │国债ETF│  │
│ └────────┘ └────────┘ └──────┘  │
│                                  │
│ Earliest trade date  ...         │
│ Latest trade date    ...         │
└──────────────────────────────────┘
```

Badge 容器为 `flex-wrap` 行内流，每个 badge 两行：
```
symbol   ← --text-label, --color-paper
name     ← --text-micro, --color-fog
```

### 5. Badge 样式

使用现有 design tokens，不新增颜色变量：

```css
.etf-badge-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
  margin: var(--spacing-12) 0;
}

.etf-badge {
  background: var(--surface-carbon);
  border: 1px solid var(--color-graphite);
  border-radius: var(--radius-sm);
  padding: var(--spacing-4) var(--spacing-8);
  text-align: center;
}

.etf-badge-symbol {
  display: block;
  font-size: var(--text-label);
  font-weight: var(--font-weight-medium);
  color: var(--color-paper);
  line-height: var(--leading-label);
}

.etf-badge-name {
  display: block;
  font-size: var(--text-micro);
  color: var(--color-fog);
  line-height: var(--leading-caption);
}
```

### 6. 测试策略

- **后端 `tests/test_dashboard.py`**：mock `_get_market_data_status()` 返回的 `etf_list`，验证序列化后包含预期的 3 个字段
- **前端 `client.test.ts`**：`createDashboardResponse()` 中新增 `etf_list` mock 数据
- **前端 `App.test.tsx`**：验证 badge 列表中至少一个 ETF 的 symbol + name 被渲染

## Risks / Trade-offs

- **[数据一致性] `covered_etfs` 和 `etf_list.length` 可能不一致** → 两者来自同一次 session 查询，但两次查询间数据可能发生变化。可接受，dashboard 为近实时快照，非事务边界
- **[ETF name 截断] 中文 ETF 名称较长（如"标普 500ETF"）** → badge 宽度由内容决定，`flex-wrap` 自动折行，不使用固定宽度或截断
- **[数量增长] 后续 ETF pool 扩展到 50+** → badge 流会很长，届时再引入截断/展开机制。当前 ≤9 不处理
