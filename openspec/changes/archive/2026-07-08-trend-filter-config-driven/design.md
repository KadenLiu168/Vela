## Context

趋势过滤链路当前由三处硬编码耦合而成：

```
config/strategy_v1.yaml (120/above)
        │
        ▼
strategy_config.py  Literal[120] / Literal["above"]   ← 加载期锁死
        │
        ▼
trend_filter.py     moving_average_days == 120         ← 字面量覆盖配置
                    price_relation == "above"            （:43-44 读取的配置被丢弃）
        │
        ▼
market_price_moving_average.py  MOVING_AVERAGE_WINDOW=120  ← 窗口写死
                                只返回 ma_120d               （窗口跟不动配置）
```

默认 120 / above 下三者取值一致，结果正确（latent）；但配置项对外"可配置"是假象。本设计让"配置 -> 均线窗口 -> 过滤判断"整条链路真正由 config 驱动，且默认路径逐字节等价。

## Goals / Non-Goals

**Goals:**
- `TrendFilterConfig` 真正可配置：窗口支持 `{60, 120, 250}`、比较方向支持 `{above, below}`，集合外 fail-fast。
- 移动均线窗口由配置驱动：`calculate_market_price_moving_average` 按请求窗口取价计算。
- `apply_trend_filter` 删除字面量守卫，比较方向与窗口均取自 `config.trend_filter`。
- 默认 120 / above 路径与修复前逐字节等价（回归零差异）。
- 显式记录等值边界语义（价 == 均线时 above / below 均不通过）。

**Non-Goals:**
- 不引入交易日历（252 vs 250 的精确化留给后续）。
- 不改变 `TrendFilterResult` 形状（字段名/类型不变），避免波及下游 `strategy_signal_generation.py`。
- 不改变 `config/strategy_v1.yaml`（120 / above 仍在合法集内）。
- 不处理 `(etf_id, trade_date)` 重复行导致的排序非确定性（既有行为，非本次回归）。

## Decisions

### 决策 1：schema 用闭集 `Literal[60, 120, 250]` / `Literal["above", "below"]`，而非开放 `int`

**理由**：fail-fast，typo 或无意义窗口在加载期即 `ValidationError`，与既有"unsupported trend filter 被拒"spec 契约一致，也和 `RebalanceConfig.frequency` 的闭集模式同构。开放 `int = Field(gt=0)` 会重新引入"配置被读但比较写死"那一类静默失效的温床。

**备选**：
- `int = Field(gt=0, le=1000)`：更灵活，但失去 fail-fast，且 250-arbitrary 的争议并不消失，只是转移。
- `Literal[60, 120, 252]`（252 = 美股交易日/年精确值）：拒绝，代码库无交易日历模块，252 是虚假精度；250 是常用整数代理。后续若引入交易日历再议。

### 决策 2：`window` 为必填关键字参数，无默认值

**理由**：强制每个调用方显式声明窗口。若给默认值 120，等于把"配置被忽略"的陷阱换个地方复活--这正是本次要消除的根因。

**备选**：`window: int = 120`。拒绝，理由同上。

### 决策 3：字段 `ma_120d` 改名 `ma`，并新增 `window` 字段

**理由**：当窗口为 60 时，字段名叫 `ma_120d` 是谎言。改名 `ma` + 携带 `window` 使结果自描述。**BREAKING**，但 grep 确认生产侧唯一读取方是 `trend_filter.py`（随本次同步改），下游 `strategy_signal_generation.py` 只读 `TrendFilterResult.passes_filter`，不受影响。测试侧 `test_market_price_moving_average.py` 同步改写。

### 决策 4：比较用严格 `>` / `<`，等值即不通过

**理由**：保留既有等值边界语义（原 `current_price > ma_120d` 即严格大于）。above 与 below 均严格，避免"等值同时满足 above 和 below"的歧义。在 spec 与变更说明中显式记录。

### 决策 5：默认 120 / above 逐字节等价的保证方式

- `window=120` -> `.limit(120)` == 原 `.limit(MOVING_AVERAGE_WINDOW)`。
- `relation="above"` -> `current_price > ma_value` == 原 `current_price > moving_average.ma_120d`。
- `ma_value` 为 120 行均价 == 原 `ma_120d`。
- 护栏 `len(prices) < window or prices[0].trade_date != as_of_date` 短路语义与原 `len < 120 or ...` 同构（`len < window` 先短路，`prices[0]` 不会越界）。

故默认配置下 `passes_filter` 与 `moving_average` 取值与修复前完全一致。

## Risks / Trade-offs

- **[BREAKING 公开 API]** `MarketPriceMovingAverage.ma_120d` 改名、`calculate_market_price_moving_average` 新增必填 `window` -> Mitigation：生产唯一消费方 `trend_filter.py` 同步更新；测试改写；grep 确认无其他生产读取方。
- **[闭集限制未来窗口]** `Literal[60,120,250]` 阻止临时窗口 -> Mitigation：故意的 fail-fast；新增窗口走一次小 change（单行修改），成本低、可审计。
- **[250 非精确交易年]** -> Mitigation：文档标注为近似值；无交易日历模块前 252 是虚假精度。
- **[`.limit(window)` 排序非确定性]** 若存在重复 `(etf_id, trade_date)` 行，`order_by(trade_date.desc())` 内部顺序不定 -> Mitigation：既有行为，非本次回归；依赖 `MarketPrice` 的 `(etf_id, trade_date)` 唯一性（超出本次范围）。
- **[未来新增 `price_relation` 漏接比较]** -> Mitigation：闭集 `Literal` 意味着新增方向必须同时改 schema 与 `apply_trend_filter` 的单一比较表达式，类型系统 + 单点比较使静默遗漏难以发生。

## Migration Plan

- 单次变更，无数据迁移、无配置改动（`strategy_v1.yaml` 保持 120 / above，仍合法）。
- 部署：合入 PR；测试全绿（含新增 below / 60 日用例）。
- 回滚：revert 提交即可，无状态需恢复。

## Open Questions

- 无阻塞项。（可选项：250 是否改为 252 -- 延后；在引入交易日历模块时一并处理。）
