## Why

当前 web 前端使用了两套字体（Inter Variable + IBM Plex Mono），但经过前一轮统一后仍存在跨字体类型的层级问题：卡片标题（`--font-display` = IBM Plex Mono）和卡片主数值（`--font-inter-variable` = Inter Variable）使用了不同字体，导致同一卡片内"Latest signal"（等宽）与"Signal #2"（非等宽）视觉不协调。用两套字体制造层级在实践上导致了不一致，且 44KB 的 IBM Plex Mono 字体加载对页面性能来说是额外负担。统一为 Inter Variable 单字体系统可以消除所有字体混合问题，用字重和字号制造层级。

## What Changes

1. **删除 IBM Plex Mono 字体** — 移除三个 @font-face 声明及其 woff2 字体文件
2. **`--font-display` token 指向 Inter Variable** — 标题元素改用 Inter Variable SemiBold，通过更大字重替代字体家族切换
3. **`--font-berkeley-mono` token 指向 Inter Variable** — 数据元素改用 Inter Variable Medium + tabular-nums，通过字重和数字特性对齐替代字体切换
4. **更新 design-system spec** — 反映新的单字体 token 值链
5. **清理文档注释** — styles.css 和 tokens.css 中的字体文档
6. **精简字体文件** — 减少 44KB 字体体积（IBM Plex Mono 三个 woff2）

## Capabilities

### New Capabilities

_无 — 这是设计系统内部的精简优化，不引入新能力。_

### Modified Capabilities

- `design-system`: `--font-display` 和 `--font-berkeley-mono` 的 token 值链改为指向 Inter Variable。
- `card-type-scale`: 无 requirement 变化，仅字体族消费值随 token 变化自动切换。
- `detail-page-typography-consistency`: 无 requirement 变化，仅字体族消费值随 token 变化自动切换。

## Impact

- **前端体积**：-44KB（删除三个 IBM Plex Mono woff2）
- **CSS**：5 处 `var(--font-display)` + 12 处 `var(--font-berkeley-mono)` 消费者无需修改代码，token 值变化自动继承
- **字体加载**：`index.html` 中 IBM Plex Mono 的 preload 需移除
- **视觉影响**：标题渲染从等宽 IBM Plex Mono 切换为 Inter Variable SemiBold，字符宽度变窄，字号可保持不变；数据区域渲染从等宽切换为比例字体，需要 `font-variant-numeric: tabular-nums` 保持数字列对齐（已有）
- **设计系统 spec**：需更新 `design-system` spec 中字体 token 相关的 requirement
- **不再依赖 IBM Plex Mono**：字体文件夹清除三个 woff2 文件，清除 preload 链接
