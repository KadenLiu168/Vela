## Context

`apps/web/` 前端测试套件有 2 条永续失败：`App.test.tsx` 中 3 行断言因 coverage timeline UI 多次重构（`7c0cef41`、`5c443e42`、`45ebfbf0`）而偏离 DOM 实际结构，从未被纠正。

## Goals / Non-Goals

**Goals:**
- `npx vitest run` 全量通过（0 failures）

**Non-Goals:**
- 不升级或降级 vitest/jsdom 版本
- 不替换测试框架
- 不改动业务代码或 UI

## Decisions

### Decision 1: 逐行修正断言而非重写测试

修正 3 处断言：

| 行号 | 当前（错误） | 修正 | 理由 |
|------|-------------|------|------|
| 38 | `getByText("Earliest trade date")` | `getByText("Earliest")` | DOM 中 label 是独立 span，文本为 "Earliest"，不是 "Earliest trade date" |
| 40 | `getByText("Latest trade date")` | `getByText("Latest")` | 同上 |
| 224 | `getAllByText("n/a").toHaveLength(2)` | `queryAllByText("n/a").toHaveLength(0)` | (a) 当日期为 null 时 coverage timeline 不渲染 → 0 个 "n/a"；(b) `getAllByText` 0 匹配会抛异常，需改用 `queryAllByText` |

### Decision 2: 不复现 jsdom 环境初始化问题

探索阶段观察到 vitest + jsdom 27 偶发环境初始化失败（`document is not defined`），但经多次稳定复现确认：当 node_modules 完整、lockfile 正确时，jsdom 27 + vitest 4.1 稳定工作。之前的 66 条失败是由 `npm install` 破坏 node_modules 导致，非 jsdom 版本兼容性问题。

## Risks / Trade-offs

- 无风险。改动仅涉及测试断言，不影响任何生产代码。
