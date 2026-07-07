## Context

Web 前端当前设计系统定义了三组字体 token：`--font-inter-variable`（Inter Variable，正文/UI）、`--font-berkeley-mono`（JetBrains Mono，数据/代码）、`--font-display`（IBM Plex Mono，标题）。实际加载了三套 woff2 字体，其中 JetBrains Mono 和 IBM Plex Mono 同为 humanist monospace，视觉差异微弱，导致页面在"哪里用哪个 mono"上缺乏可感知的层级逻辑。

本 change 将等宽字体统一为 IBM Plex Mono，形成"Inter Variable（正文）+ IBM Plex Mono（标题、数据、标签）"的双字体系统，用字重和尺寸制造层级。

## Goals / Non-Goals

**Goals:**
- 消除 JetBrains Mono 和 IBM Plex Mono 的视觉混淆
- 将字体系统从 3 套精简为 2 套（Inter Variable + IBM Plex Mono）
- 减少 182KB 字体加载体积
- 保持所有消费者（14处 `var(--font-berkeley-mono)`）代码零修改
- 更新 `design-system` spec 以反映新的 token 值链
- 标题（SemiBold 600）vs 数据（Medium 500）vs 标签（Regular 400）的三级 mono 层级清晰可辨

**Non-Goals:**
- 不改变 font-size、letter-spacing 等数值 token
- 不增加新字体或删除 Inter Variable
- 不影响后端、API、数据库
- 不改变 Ladle（storybook 组件库）的字体
- 不涉及付费字体购买（Berkeley Mono / Söhne Mono 仍是设计意图，但不加载）

## Decisions

### 决策1：保留 IBM Plex Mono 而非 JetBrains Mono

- IBM Plex Mono 已有 3 个字重（400 / 500 / 600）44KB，weight 跨度大，具备用字重制造层级的弹性
- JetBrains Mono 只有 2 个字重（400 / 500-600）182KB，且字宽更窄 — 在密集数据显示中有优势，但以增加一个字体为代价不划算
- IBM Plex Mono 的字宽更接近传统 printing mono 的比例，与 Inter Variable 的对比更强

### 决策2：`--font-berkeley-mono` token 指向 IBM Plex Mono 而非移除 token

- token 名称 `--font-berkeley-mono` 遵循设计意图命名原则（spec requirement），不应因实际加载字体变化而改名
- 保持 token 名称不变，14 处消费者零修改
- 若将来加载真正的 Berkeley Mono，只需更换 token 值，消费者不变

### 决策3：`--font-display` 和 `--font-berkeley-mono` 解耦为同一字体的不同用途

- 两个 token 都指向 IBM Plex Mono，但语义不同：
  - `--font-display`：标题（通常 SemiBold 600，更大字重）
  - `--font-berkeley-mono`：数据/代码（通常 Regular 400 / Medium 500，更小阅读尺寸）
- 未来如果加载真正的 Söhne Mono（标题）和 Berkeley Mono（数据），两个 token 可以独立切换

### 决策4：保留所有 3 个 IBM Plex Mono 字重文件

- Regular（400）、Medium（500）、SemiBold（600）各 14-15KB，总 44KB
- 移除后节省有限（最大 15KB），但失去的层级表达力不值得
- 三个字重刚好对应：标签(Regular) → 数据(Medium) → 标题(SemiBold) 的三级

## Risks / Trade-offs

- **[布局风险]** IBM Plex Mono 字宽约 1.23x（vs JetBrains Mono 约 1.0x），数据密集区域（ETF 代码、时间戳、数值列）字符可能变宽导致截断 → **缓解**：`apps/web/src/index.html` 已 preload IBMPlexMono-Regular 和 -Medium，不会 flash-of-invisible；建议实施后检查 `.holdings-table td`、`.parameter-summary`、`.compact-list dd` 等密集区域的 overflow 情况
- **[下载量增加]** Inter Variable（338KB）目前已经占主导，IBM Plex Mono 的 44KB 与 JetBrains Mono 的 182KB 相比实际减少 138KB 总体积，是对性能的净改善
- **[Ladle 字体]** Ladle storybook 环境使用了 Arial/system 字体，不在此 change 范围内，不影响

## Migration Plan

无需分阶段迁移 — 此 change 是纯 CSS token 值变更 + 字体文件清理，单次部署即可完成。原子性保证：所有消费者通过 token 间接引用，token 值变化后自动生效。

**回滚策略**：保留 JetBrains Mono 的 woff2 文件至下次清理，回滚时恢复 `@font-face` 规则和 token 值即可。
