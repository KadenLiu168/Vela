## Why

市场数据层存在一个影响正确性的根基 bug:三个 provider 全部以未复权模式抓取(`adjust=""` / `fq=None`),`base_market_data_provider` 硬编码 `adjusted_close=None`,导致 `MarketPrice.adjusted_close` 永远为 NULL,`strategy_price` 永远回退到未复权 `close_price`。任何发生过分红/拆股的 ETF,其动量/趋势/净值信号在跳变后的价格序列上计算,直接失真。该行为目前被 `market-data-provider` spec 的三条 "unadjusted by default" scenario 明文锁定,修复必须同步改 spec。

## What Changes

- **BREAKING**:市场数据存储口径从"未复权价 + 永远为空的 adjusted_close"改为"未复权价 `close_price` + 后复权因子 `factor_hfq`(append-only)"。
- **BREAKING**:`MarketPrice.adjusted_close` 列删除,新增 `factor_hfq Numeric(18,12) NOT NULL` 列。一个 Alembic migration。
- **BREAKING**:`MarketPrice.strategy_price` 语义从"`adjusted_close ?? close_price`(未复权回退)"改为"`close_price * factor_hfq`(后复权)"。
- 三个 provider(akshare / tencent / joinquant)改为后复权模式抓取并暴露复权因子:
  - joinquant `get_price(fq=None, fields=[..., "factor"])` -- 未复权 OHLC + factor 字段同时返回,直接得因子,无需 /factor 还原。
  - akshare `fund_etf_hist_em(adjust="hfq")` / tencent `stock_zh_a_hist_tx(adjust="hfq")` -- 抓未复权 + 后复权两次,反推 `factor = 后复权 / 未复权`。
- 新增前复权价查询函数,口径 A(查询时现算,不落库不缓存):`qfq(D) = 后复权(D) / 后复权(T)`,T 为调仓日。用于信号生成与回测信号计算。
- 信号生成与回测信号计算使用前复权价;回测成交使用未复权 `close_price`;回测净值使用后复权 `strategy_price`(选项 Y,分红再投隐含,净值无跳变)。
- 增量更新每次校验因子一致性:比对存量最后一行 `factor_hfq` 与上游同日因子值,不等则触发该 ETF 全量重抓(检测公司行动以给新行正确因子)。方案 B 的 append-only 因子快照免疫上游 retroactive 因子修正,故该校验唯一目的是检测公司行动,而非防上游漂移。
- 数据初始化策略:重置 `market_price` 表 + 全量重抓,消除存量回填问题(无旧行混合口径)。
- `market-data-provider` spec 三条 "unadjusted by default" scenario 改为"后复权 by default + 暴露因子"。

## Capabilities

### New Capabilities

- `adjusted-price-projection`: 前复权价查询投影能力。定义如何从存储的未复权价 + 后复权因子现算前复权价序列(口径 A),以及信号/成交/净值三种价格口径的分工契约。

### Modified Capabilities

- `market-data-provider`: 三个 provider 从未复权改为后复权抓取并暴露复权因子;`DailyPrice` 契约新增 factor 字段;三条 "unadjusted by default" scenario 改为后复权。
- `market-data`: `MarketPrice` 存储模型删除 `adjusted_close`、新增 `factor_hfq`;`strategy_price` 语义从"adjusted_close 回退"改为"后复权 close_price × factor_hfq";provider→MarketPrice 映射改 factor;增量更新新增因子一致性校验(检测公司行动)与触发全量重抓。

> 注:momentum-scoring / trend-filtering / strategy-equity-curve 的 requirement 文本使用抽象"strategy price",底层定义变更后行为契约(用 strategy_price 算比值/净值)不变,故不改其 spec;数值变化(净值含分红)是修复目的,非契约变更。这些 capability 实现层自动跟随 `strategy_price` 语义,无需 delta。

## Impact

- **代码**:
  - `packages/core/src/vela_core/`:三个 provider、`base_market_data_provider`、`market_data_provider`(DailyPrice)、`market_price_mapping`、`models/market_price`、`market_data_fetcher`(增量校验+重抓)、信号层(momentum/trend/returns/moving_average)、`strategy_equity_curve`。
  - 新增前复权投影查询模块。
  - `apps/cli`、`apps/api`:provider 构造与 fetch workflow 调用点。
- **数据库**:一个 Alembic migration(drop `adjusted_close`,add `factor_hfq`)。重置 `market_price` 表 + 全量重抓。
- **依赖**:无新增第三方依赖,复用现有 akshare/jqdatasdk。
- **测试**:provider 测试需改 mock(后复权返回值 + factor 列);新增前复权投影、复权一致性校验、公司行动触发重抓的测试;信号层测试因价格口径变更需调整预期值。
- **运维**:首次上线需重置 `market_price` + 全量重抓;旧的 `strategy_signal` / `backtest` 记录基于错误未复权价,建议一并清理(上线时定,不影响设计)。
- **Spec**:`market-data-provider`、`market-data`、`momentum-scoring`、`trend-filtering`、`strategy-equity-curve` 五个 capability 的 delta。
