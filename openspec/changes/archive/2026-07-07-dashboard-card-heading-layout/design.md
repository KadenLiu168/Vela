## Context

Dashboard 6 张卡片共享 `PanelHeading` 组件，其布局为 `justify-content: space-between`，将 eyebrow（<span>，灰色小字全大写）置于左侧、title（<h3>，白色大字）置于右侧。这种排列导致视觉阅读起点（左侧）是最轻的元素，而视觉重量最大的元素却在右侧——每个卡片头都呈现「头重脚轻」的失衡感。

## Goals / Non-Goals

**Goals:**
- 将 title（白色大字）移至卡片左侧，作为自然阅读起点
- 将 eyebrow（灰色小字）移至右侧，作为补充分类
- Signal / Backtest / Fetches 三张卡片移除 eyebrow（已有 statusPill 提供辅助信息）
- 更新内容对以匹配新布局的角色定位
- 保持 statusPill 紧跟在 title 右侧

**Non-Goals:**
- 不改动 statusPill 的样式或逻辑
- 不涉及其他页面的 heading

## Decisions

| Decision | Rationale |
|----------|-----------|
| `eyebrow` 改为可选参数 | Signal/Backtest/Fetches 不需要分类标签，删除后使 JSX 更干净 |
| 新增 `.panel-heading-start` 替代 `.panel-heading-end` | 布局结构倒转：title + pill 在左（`flex-start`），eyebrow 在右 |
| Market title 回到 `Market data` | 反转后 title 占据阅读主位，「Market data」比「Price data」更符合卡片主要角色 |

## 新旧布局对比

```
当前:
┌──────────────────────────────────────────┐
│ MARKET                       Price data  │  ← 左轻右重
│                                           │
│ Price rows · Covered ETFs                 │
└──────────────────────────────────────────┘

方案 B:
┌──────────────────────────────────────────┐
│ Market data                     PRICE     │  ← 左重右轻
│                                           │
│ Price rows · Covered ETFs                 │
└──────────────────────────────────────────┘

Signal (去掉 eyebrow):
┌──────────────────────────────────────────┐
│ Latest signal  [Active]                  │
│                                           │
│ Signal #42 · 2026-06-23 · rebalance      │
└──────────────────────────────────────────┘
```

## Risks / Trade-offs

- 无风险。纯布局反转 + 可选参数调整，不影响功能或数据流
