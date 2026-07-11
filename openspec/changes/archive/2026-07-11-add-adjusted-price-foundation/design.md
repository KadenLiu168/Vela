## Context

Vela 的市场数据层当前以未复权价格存储并供策略层消费。三个 provider(akshare `fund_etf_hist_em`、tencent `stock_zh_a_hist_tx`、joinquant `get_price`)全部以 `adjust=""` / `fq=None` 抓取,`base_market_data_provider._extract_row` 硬编码 `adjusted_close=None`,导致 `MarketPrice.adjusted_close` 永远为 NULL,`strategy_price` property 永远回退到未复权 `close_price`。策略层(momentum / trend / returns / moving_average / equity_curve)全部消费 `strategy_price`,因此在任何发生过分红/拆股的 ETF 上,信号在跳变后的价格序列上计算,失真。

该行为被 `market-data-provider` spec 三条 "unadjusted by default" scenario 明文锁定,修复须同步改 spec。

复权模式能力边界(已核实三个源签名):
- akshare `fund_etf_hist_em(adjust ∈ {"qfq","hfq",""})`:设复权后 OHLC 整体替换为复权值,不新增 adjusted_close 列。
- tencent `stock_zh_a_hist_tx(adjust ∈ {"qfq","hfq",""})`:同上,返回列仍 date/open/close/high/low。
- joinquant `get_price(fq ∈ {"pre","post",None}, fields=[...,"factor"])`:设复权后 OHLC 整体替换;额外暴露 `factor` 字段(每日复权因子,append-only 语义)。

## Goals / Non-Goals

**Goals:**
- 消除分红/拆股导致的价格跳变对策略信号与回测净值的失真。
- 存储模型 append-only:复权因子一旦写入永不修改,存量历史永不过期,回测可复现。
- 明确三种价格口径的分工:前复权(信号)、未复权(成交)、后复权(净值)。
- 增量更新自带公司行动检测,无需额外分红事件数据源。

**Non-Goals:**
- 不显式建模分红现金流(选项 X);分红再投通过后复权因子隐含处理。
- 不引入新的第三方数据源;复用现有 akshare / jqdatasdk。
- 不做前复权物化缓存(会重新引入漂移,违背 append-only 初衷)。
- 不在本 change 中实现前端价格图展示(前复权投影函数就绪即可,展示层后续接入)。

## Decisions

### Decision 1: 方案 B 存储 -- 未复权价 + 后复权因子(append-only)

存储 `close_price`(未复权真实价)+ `factor_hfq`(后复权因子)。复权价按需现算。

**Why B over A(存后复权价)**:方案 A 存的是派生值(未复权 × 因子),依赖上游复权因子永远自洽;偶发的上游因子追溯修正会让存量历史中段失配,且方案 A 的"最后一行一致性校验"对历史中段漂移有盲区。方案 B 存两个原始事实(未复权价 + 因子),公司行动只追加新因子行、永不修改旧行,存量永不过期,无需回填。

**Alternatives considered**:
- 方案 A(存后复权价 + 一致性校验 + 回填):简单,但中段漂移盲区 + 持续回填运维负担。
- 方案 A 前复权存储:排除 -- 前复权锚定"今天",每次公司行动全量历史重算,与入库后计算模型根本冲突。

### Decision 2: 因子存储类型必须用后复权因子

前复权因子的"锚点=今天"会随时间移动,每次公司行动需重写全部历史因子行,破坏 append-only。后复权因子锚定上市首日,公司行动只影响新行。

**前复权作为查询投影,不存储**:前复权价 = 后复权(D) / factor_hfq(T),T 为调仓日(后复权(D) = close(D)·factor(D);除以 factor(T) 使 qfq(T) = close(T) 自洽)。纯查询时计算,不落库不缓存。

### Decision 3: 信号用前复权、成交用未复权、净值用后复权(选项 Y)

- **信号生成 / 回测信号**:前复权价(现算,口径 A)。消除分红跳变的连续价格视角。
- **回测成交**:未复权 `close_price`。真实撮合价。
- **净值**:后复权 `strategy_price`(选项 Y)。后复权因子隐含分红再投,净值无跳变,正确。

**自洽点**:调仓日 T 的前复权"当前价" `qfq(T) = close(T)·factor(T)/factor(T) = close(T)` 恰等于未复权成交价,信号判断与成交执行在单次调仓内同量纲。

**为什么不选净值选项 X(未复权市值)**:未复权成交价不包含分红现金流,净值在分红日会出现虚假跳跌,等于把跳变失真从信号侧挪到净值侧,与修复初衷矛盾。选项 Y 用后复权隐含分红再投,净值连续正确。

### Decision 4: 前复权用口径 A(查询时现算),禁止物化缓存

前复权有跨行依赖(归一化基准 = 调仓日后复权价),today 基准随公司行动变化。一旦物化缓存,基准变后所有历史行缓存失效,重新引入漂移。故前复权只能现算,不落库不缓存。

### Decision 5: 动量类比值信号,前复权与后复权数值等价(关键推论)

```
前复权(D) = 后复权(D) / factor_hfq(T)   ← 只差归一化常数 factor_hfq(T)

动量 = 当前价/历史价 - 1  (比值信号)
     = [后复权(T)/C] / [后复权(D)/C] - 1     (C = 后复权(T),常数约掉)
     = 后复权(T)/后复权(D) - 1
     = 用后复权算的结果
```

含义:对 momentum / trend / returns 这类**比值信号**,"信号用前复权"与"信号用后复权"算出的信号数值相同,前复权只在价格图展示上有视觉差异。因此策略层实际可继续读 `strategy_price`(后复权),信号数值不变 -- 改动量比表面小。前复权投影函数主要为未来展示层与对账场景就绪。

### Decision 6: 增量更新每次校验因子一致性,公司行动则全量重抓该 ETF

每次增量 fetch 后,比对存量最后一行(D_last)的 `factor_hfq`(我们自己存的快照)与上游同日返回的因子值(joinquant 直接给 `factor` / akshare·腾讯由后复权÷未复权反推):
- 相等(相对误差 < 1e-6):因子未变,沿用存量因子给新行,append 新行。
- 不等:公司行动发生在 D_last 之后(或上游修正了因子),触发该 ETF 全量重抓(append-only 重写因子序列,旧行不动)。

**关键区别于方案 A 的校验语义**:方案 A 存的是派生值(后复权价),校验"后复权价漂移"是为防上游 retroactive 因子修正;方案 B 存两个原始事实(未复权价 + 因子快照),append-only 因子快照**天生免疫**上游 retroactive 因子修正 -- 已存的因子行永不被上游改写。故方案 B 的该校验**唯一目的是检测公司行动以给新行正确因子**:增量只抓未复权价(1× fetch),无法得知因子是否变化,必须比对才能发现公司行动并更新新行因子。

**Why 比对因子而非比对后复权价**:存的就是因子,直接比对因子比"算后复权价再比对"更直接、更便宜(免一次乘积),且语义准确(检测对象就是因子变化,不是派生价)。

**Why 比对公司行动事件而非订阅事件流**:零额外数据源,用已有行情接口即可检测。检测发生在下次拉取(滞后一个交易日),对日频动量策略可接受。

一致性校验复用现有 `data_fetch_log.quality_warnings` 架构,与交易日缺口、重复 trade_date 检测并列(同构扩展)。

### Decision 7: 数据初始化 -- 重置 market_price + 全量重抓

修复上线时重置 `market_price` 表,对每个 ETF 从上市日全量重抓(joinquant 1× fetch 含 factor;akshare/腾讯 2× fetch 反推 factor),入库新口径数据。

**Why 重置而非渐进回填**:无旧行混合口径,无历史中段因子追溯盲区,DB 全部行为新口径,一次到位。代价是丢失现有 market_price 历史,但该历史本就要被新口径替换。旧 `strategy_signal` / `backtest` 记录因基于错误未复权价,建议一并清理(上线时定)。

### Decision 8: factor 精度 Numeric(18,12)

复权因子是浮点比例(如 1.1025),需高精度避免累积误差。`close_price × factor` 后落库到 `Numeric(18,6)` 价格列。因子列 `factor_hfq Numeric(18,12) NOT NULL`。

## Risks / Trade-offs

- **[akshare/腾讯因子反推精度]** -> 反推 `factor = 后复权 / 未复权` 受两源 rounding 差异影响。Mitigation:一致性校验用相对误差 1e-6 容差,非精确相等;joinquant 作为基准源(factor 直接给,最可靠)。
- **[2× fetch 失败面]** akshare/腾讯需两次 fetch 反推因子,任一失败整批失败。Mitigation:复用现有 tenacity 重试;首次构建是一次性成本,日常增量只抓未复权(1×)。
- **[公司行动检测滞后]** 公司行动在下次增量校验才检测,滞后一个交易日。Mitigation:方案 B 下旧行因子快照不受影响,只有公司行动后的新行因子可能短暂错误直到下次校验修正;日频策略可接受;若需更及时可加周期性抽样校验。
- **[重置 DB 丢失旧数据]** 重置 market_price 丢失历史;旧 strategy_signal/backtest 基于错误价格。Mitigation:历史数据本就要替换;旧信号/回测记录建议一并清理(design 不强制,上线时定)。
- **[strategy_price 语义变更]** 从"未复权回退"变为"后复权",数值会变。Mitigation:对比值信号数值不变(Decision 5);信号层测试需调整预期值;净值口径明确为后复权。
- **[close_price 列语义误导]** close_price 仍是未复权(正确),但策略层不再直接用它(用 strategy_price 后复权)。Mitigation:文档注明 close_price=未复权真实价(成交用);adjusted_close 列删除消除旧的误导。

## Migration Plan

1. Alembic migration:drop `adjusted_close`,add `factor_hfq Numeric(18,12) NOT NULL`。
2. 改 provider / base_provider / mapping / model / 信号层 / 净值层代码。
3. 重置 `market_price` 表。
4. 全量重抓:每 ETF 从上市日 fetch,得 close_price + factor_hfq,入库。
5. (建议)清理旧 strategy_signal / backtest 记录。
6. 跑全量测试,验证信号数值(比值信号应与旧值在无公司行动区间一致)。

**Rollback**:回退 migration(restore adjusted_close, drop factor_hfq)+ 回退代码 + 重抓未复权数据。回滚后回到 bug 状态(未复权),数据可用但信号失真。

## Open Questions

- 旧 `strategy_signal` / `backtest` 记录是否在上线时一并清理?(建议清理,但不影响设计;上线时定)
- 公司行动检测的相对误差容差 1e-6 是否合适?(实现时用真实分红数据校准)
