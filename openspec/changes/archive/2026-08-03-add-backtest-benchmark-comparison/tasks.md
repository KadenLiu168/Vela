## 1. Core benchmark calculation and persistence

- [x] 1.1 为固定的同池月度等权和 `SSE:510300` 买入持有基准编写确定性数值测试，覆盖首日无成本、月末调仓、成本、前复权价格比率和完整共同日期。
- [x] 1.2 实现独立的 benchmark 曲线/指标计算模块，复用现有指标函数和官方交易日轴，并在缺少或未激活 `SSE:510300` 及任一必需价格时 fail-fast。
- [x] 1.3 增加 benchmark ORM 模型、关系、Alembic migration 和文件型 SQLite 升降级/持久化测试，确保旧回测可读且无基准集合。
- [x] 1.4 扩展回测结果持久化输入、查询预加载和报告格式，使新回测原子地保存两条基准及曲线、导出报告显示其指标和收益差值。

## 2. Backtest and Walk-forward orchestration

- [x] 2.1 扩展 `run_backtest` 结果与编排：普通运行计算双基准，IS 参数试跑显式跳过，OOS 运行计算并持久化双基准；补充调用顺序、失败回滚和 rerun 隔离测试。
- [x] 2.2 移除 Walk-forward 配置的 `baseline` 模型/YAML/旧报告字段，改为读取每个 OOS run 的固定双基准结果。
- [x] 2.3 扩展 Walk-forward 窗口结果与文本报告，逐窗显示双基准指标/总收益/CAGR 差值，并汇总每条基准差值的均值与有效窗口数；添加多窗口数值与缺失 510300 测试。

## 3. API and CLI contracts

- [x] 3.1 扩展 FastAPI schema、router 和 API client 类型：回测运行/详情返回有序 benchmark 条目、五项指标、相对收益差值和详情曲线；旧 run 返回空集合。
- [x] 3.2 补充 API 合同与集成测试，验证两条固定 key、曲线日期排序、差值、legacy 空集合和 benchmark 缺数失败响应。
- [x] 3.3 更新 `run-backtest` CLI 摘要及 CLI 回归测试，确认双基准指标与差值被输出且现有错误处理不变。

## 4. Backtest detail presentation

- [x] 4.1 将纯 equity-chart geometry 扩展为可测试的多序列输入，同时保持现有单策略、空和单点显示行为。
- [x] 4.2 更新回测详情页，显示两组有名称的基准指标/差值以及有图例的三线净值图；不改变 Dashboard 摘要和回测列表。
- [x] 4.3 更新前端 API fixtures、组件和纯 geometry 测试，覆盖三线图、legacy 空基准、加载/错误状态及可访问图例。

## 5. Validation and specification completion

- [x] 5.1 对新增 migration、核心计算、回测、Walk-forward、API、CLI 和 Web 运行针对性测试，并使用测试自有数据库验证完整失败不留下部分结果。
- [x] 5.2 运行 `openspec validate add-backtest-benchmark-comparison --strict`，修正所有 Change artifact 问题。
- [x] 5.3 在最终代码稳定后运行完整 Python gate 与完整 Web gate，并将命令和结果记录在交接说明中。
