## Context

上一轮统一（移除 JetBrains Mono）后，当前字体系统为 Inter Variable + IBM Plex Mono。但实际使用中，`--font-display`（标题，IBM Plex Mono）与 `--font-inter-variable`（正文/UI，Inter Variable）的混合导致同卡片区域内字体不统一（标题等宽、数值非等宽）。此外 IBM Plex Mono 的 44KB 字体加载对性能有额外开销。

本 change 将全站统一为 Inter Variable 单字体，用字重和数字特性替代字体家族切换来制造层级。

## Goals / Non-Goals

**Goals:**
- 全站所有元素使用 Inter Variable 一种字体
- 移除 IBM Plex Mono 的所有 @font-face 声明、woff2 文件和 preload
- 保持 `--font-display` 和 `--font-berkeley-mono` token 名称不变，值改为 Inter Variable
- 通过字重和字号维持视觉层级（标题 SemiBold 590 vs 数据 Medium 510 vs 正文 Regular 400）
- 通过 `font-variant-numeric: tabular-nums` 维持数字列对齐
- 减少 44KB 字体加载体积

**Non-Goals:**
- 不改变 font-size、letter-spacing、line-height 等数值 token
- 不改变 CSS 选择器或 DOM 结构
- 不影响后端、API、数据库
- 不引入新字体文件

## Decisions

### 决策1：保持三个 token 名称不变，只改值

- `--font-inter-variable`：不变，仍是 Inter Variable
- `--font-display`：值改为 `"Inter Variable", ...` 的 fallback 链
- `--font-berkeley-mono`：值改为 `"Inter Variable", ...` 的 fallback 链
- 消费者（5处 + 12处）零代码修改，仅 token 值变化自动继承
- 未来如需加入 display 字体，只需修改 token 值

### 决策2：用字重和 `font-variant-numeric` 替代字体切换

Inter Variable 支持 300–700 可变范围，足以用字重制造三层视觉层级：

| 层级 | 字重 | 语义 | 用途 |
|------|------|------|------|
| 标题 | SemiBold 590 | `--font-weight-semibold` | 页面/卡片标题 |
| 数据 | Medium 510 | `--font-weight-medium` | 数值、代码、标识符 |
| 正文 | Regular 400 | `--font-weight-regular` | 正文、标签、描述 |

数字对齐通过 `font-variant-numeric: tabular-nums` 实现，CSS 中 `.etf-row-symbol`、`.panel-primary` 等已拥有此声明。

### 决策3：移除所有 IBM Plex Mono 资源

- 删除 3 个 @font-face 规则
- 删除 `IBMPlexMono-*.woff2` 三个文件（44KB）
- 删除 `index.html` 中 IBM Plex Mono 的两个 preload 链接
- Inter Variable 的 preload 保留

## Risks / Trade-offs

- **[标题失去等宽特质]** 标题从 IBM Plex Mono（等宽）切换为 Inter Variable（比例），字符宽度不均 → **权衡**：用 SemiBold 590 + 紧凑字距（`--tracking-heading` 已有 -0.704px）补偿，标题仍然有力
- **[数据区域失去等宽对齐]** `.holdings-table td`、`.compact-list dd`、`.etf-row-symbol` 从等宽字体切换为比例字体 → **缓解**：这些选择器已设置 `font-variant-numeric: tabular-nums`，数字列可正确对齐。英文符号（如 ETF 代码 "SPY"）会变为比例宽度，但这是行业常见的 trade-off
- **[Inter Variable 下载量]** 338KB 已经在首次加载时下载，无额外开销
- **[回滚简单]** 只需恢复 IBM Plex Mono 的 @font-face 和 font 文件即可

## Migration Plan

原子性变更。同上一轮：所有消费者通过 token 间接引用，token 值变化后自动生效。单次部署。
