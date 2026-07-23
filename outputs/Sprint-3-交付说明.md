# Sprint 3 交付说明

## 结论

Sprint 3 已完成 PC 优先响应式 PWA、三际录核心页面、Owner 封闭研究试算和隐私/成本
控制。所有页面数据均为虚构 fixture。生产规则、member/viewer 推演、完整八字/紫微、
自动宿世本卦、DeepSeek 默认调用和公开部署均未启用。

## Git 基线

- PR #5 合并方式：Squash and merge
- PR #5 merge SHA：`be62dd8a3532313b409fda74fa18adcf912a5071`
- Sprint 3 分支：`feature/sprint-3-core-experience-private-research`
- Sprint 3 PR：创建后保持未合并，等待产品负责人验收

## 交付内容

- 响应式产品壳、桌面侧栏与最多五项手机底栏；
- 三际录、六象合参、三际断章、宿世星图、中阴之门、命势长图、缘契图、观照录、
  历次命卷与手机“更多”；
- Owner 研究试算入口，模板默认、DeepSeek 逐次确认；
- 脱敏 Provider 输入、Token/成本记录和可删除报告；
- PostgreSQL 迁移、RLS、OpenAPI 与 JSON Schema；
- PWA manifest、192/512 图标、安全 Service Worker；
- 响应式、隐私、权限、PWA、禁用规则与 Secret Scan 门禁；
- 文风技术债及九例回归触发条件。

## 视觉与无障碍证据

| 证据 | 验证结果 |
| --- | --- |
| `sprint3-mobile-390.png` | 390×844，无横向溢出；五项底栏；速记录入不拥挤 |
| `sprint3-tablet-768.png` | 768×1024，无横向溢出；15 个真实处理阶段 |
| `sprint3-desktop-1440.png` | 1440×900，无横向溢出；完整侧栏和仪表盘 |
| `sprint3-wide-1920.png` | 1920×1080，无横向溢出；星图及六节点列表替代 |
| `sprint3-report-1440.png` | 11 章长文与 Owner 技术细节可读 |

另以 720px 宽视口模拟 200% 缩放，并启用 `prefers-reduced-motion: reduce` 验证。
键盘焦点可见，图表状态不只依赖颜色，SVG 图表均有列表或表格替代。

## 安全结论

- 普通 CI 不读取或调用 `DEEPSEEK_API_KEY`；
- Service Worker 不缓存 API、档案、证据、日志、关系、断章、Token、Session、Prompt
  或模型响应；
- DeepSeek 只在 Owner 明确选择且逐次确认后调用；
- 外部模型只接收获准的脱敏结构化摘要；
- 模型用量表不存原始 Prompt 或响应；
- 研究报告支持幂等删除；
- 生产 ruleset 继续为 `draft` 且 `production_activatable=false`。

## 验收边界

本地环境没有 Docker/PostgreSQL 16 服务。数据库迁移、RLS、并发和 HTTP→PostgreSQL
E2E 以 Sprint 3 PR 的 GitHub Actions PostgreSQL 16 service 运行结果为最终证据。
本交付完成 PR 与 CI 后停止，不自行合并，不进入下一阶段。
