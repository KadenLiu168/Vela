## Context

Dashboard Operations 面板的 `operation-list`（`DashboardPage.tsx:380-416`）当前包含：

| 按钮 | 类名 | 档位 |
|---|---|---|
| Fetch market data | `button-secondary` | outline |
| Fetch full | `button-tertiary` | text-only |
| Generate signal | `button-secondary` | outline |
| Bootstrap / Setup | `button-primary` | filled |

`button-tertiary` 是 `design-system` 三档契约中的合法变体（styles.css:1224-1239），全站仅此一处使用。问题不在单个按钮是否合法，而在同一 `flex gap:12` 按钮组内混排三种视觉重量：text-only 按钮无边框、padding 更窄（8px vs 20px），视觉上"缩水"，容易被误读为样式缺失。代码痕迹（`title="Re-downloads all ETF price history"`）表明当初可能是想用弱化样式表达"非常规重操作"，但这种降级过于隐晦，与相邻按钮的视觉断裂反而造成困惑。

## Goals / Non-Goals

**Goals:**

- "Fetch full" 与同组按钮统一为 `button-secondary`，消除视觉断裂。
- 在 `design-system` spec 中固化"同组按钮同档位"约束，防止回归。

**Non-Goals:**

- 不删除 `button-tertiary` 变体（合法三档之一，保留供其他场景使用）。
- 不改变 "Fetch full" 的功能（完整数据重新下载）、文案与 `title`。
- 不调整 `operation-list` 的布局（flex、gap）。
- 不改动其他按钮。

## Decisions

### 决策 1："Fetch full" 改用 `button-secondary`

- 备选 A：保持 `tertiary`，把按钮移出 `operation-list` 单独成行或加说明文字。
- 备选 B：删除 "Fetch full"，合并进 "Fetch market data" 的交互。
- 选择理由：方案 A 保留弱化意图但增加布局复杂度，且"重操作弱化"的语义在界面中无其他先例；方案 B 超出本次一致性修复范围。改 `secondary` 是单点最小改动，与用户"统一视觉"的目标一致，次要性由文案 "Fetch full" 与 `title` 提示承担。

### 决策 2：在 `design-system` spec 固化同组档位约束

- 备选：只改代码不动 spec。
- 选择理由：本次问题正源于"变体选择缺乏规则"——`tertiary` 单独看完全合法，混排才产生问题。在 "Buttons follow a three-variant contract" 下补充场景，使"同一按钮组内 MUST 同档位"成为可测约束。

## Risks / Trade-offs

- "Fetch full" 从 text-only 变为 outline，视觉重量增加，可能让用户更注意这个"重操作" → 属预期效果（与相邻按钮一致）；若产品希望继续弱化，应走方案 A 并另开 change。
- `design-system` spec 的新场景与既有 "primary is the sole chromatic UI element per view" 不冲突（场景仅约束同组内 secondary 一致，primary 例外）。
- 与 P2 `extract-shared-button-component` 不冲突：P2 将按钮封装为组件时，本 change 的 `button-secondary` 选择即成为默认档位。

## Migration Plan

- 单行类名改动 + spec 场景补充，无迁移。
- 回滚：revert 类名改动即可；spec 场景属增量约束，保留或随 change 一并回滚均安全。
