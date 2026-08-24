# V1.1 全产品红蓝审计

本审计基于代码、页面、迁移、测试和既有运行证据；不把研究规则表述为传统共识。基线为 `bef1466`，三际枢、Ruleset、Profile、Golden、Replay 和 17 个受保护 Hash 均在保护范围内。

## 红队结论

| 领域 | 等级 | 发现 | 处置 | 合并影响 |
| --- | --- | --- | --- | --- |
| 产品与语言 | P1 | 普通页面仍出现 `Profile`、`research_active`、英文状态和不统一的 Strength/Confidence 译名 | 统一为“研究方法”“研究中”“象势”“证契完备度”，机器值折叠展示 | 已修复 |
| 用户旅程 | P1 | 深层页面返回路径不一致；失败时缺少关联 ID | 增加上下文返回入口和可重试、可追踪错误 | 已修复 |
| 前端稳定性 | P1 | 请求没有统一超时、取消和竞态边界 | 请求层增加 15 秒默认超时、AbortSignal、no-store 与请求 ID | 已修复 |
| PWA/隐私 | P1 | 旧离线壳缓存清理和更新提示不足 | 版本化公共壳、清理旧缓存、明确私密路径 network-only、离线页与更新提示 | 已修复 |
| API/可观测性 | P1 | 内存与 PostgreSQL 应用的错误封套及请求 ID 不完全一致 | 保留 `detail` 兼容，同时加入安全 `error` 与 `request_id`；日志只记错误类型 | 已修复 |
| 安全头 | P1 | Web/API 的 CSP、Permissions Policy、frame/referrer 约束不完整 | 增加最小安全头；生产 API 启用 HSTS | 已修复 |
| 数据库 | P2 | 可继续缩小部分 `SELECT *` 的读取面 | 现有访问均受 profile/owner/RLS 和现有索引约束；缺少真实慢查询证据，不新增 migration | 延后；不阻止合并 |
| 性能 | P2 | 无生产流量，不能声称真实 API P95 改善 | 只验证构建、Lighthouse、请求上限与无重复缓存；生产指标留待受控部署 | 只阻止夸大宣传 |
| DeepSeek | P2 | 文学质量仍有已知技术债 | 本轮不调用 Provider、不改 Prompt、不影响确定性报告 | 延后；不阻止合并 |
| 运行治理 | P2 | KMS、数据地区、备份保留与删除 SLA 仍待负责人确认 | 保持 Private/研究态，沿用部署和备份文档 | 阻止公开/生产，不阻止私有合并 |
| 许可证 | P2 | 最终代码/规则/知识许可证仍未书面冻结 | 不添加许可证、不公开、不发布 | 阻止公开，不阻止私有合并 |
| 视觉 | P3 | 新首页会引起三个平台基线的预期差异 | 只允许逐张审查受影响页面；禁止提高容差或批量接受 | 需远端证据闭环 |

P0：0。P1 均有实现与门禁。P2/P3 不改变算法或私人研究运行，已明确其公开/生产边界。

## 主动攻击结果

- 直接访问 API、主体、三际录、记录、合参、设置与 Prompt 路径时，Service Worker 不得读取或写入 Cache Storage。
- 伪造或过长的 `X-Request-ID` 不得原样进入日志或响应；服务端重新生成安全 ID。
- 上游不可用、超时、验证失败和未知异常不返回栈、请求正文、出生资料、梦境或关系正文。
- 普通用户首屏不把 Hash、Ruleset、Signal 或数据集 revision 当作结论；研究细节继续折叠。
- 未知出生时刻不会补造；研究状态不会被包装为生产共识；DeepSeek 不参与任何确定性字段。
- 现有 PostgreSQL 16 migration 已覆盖主体、记录、执行、三际录、专题和命势的 owner/profile/created_at 访问索引；无查询计划证据时不制造新索引。

## 蓝队保护

- `packages/sanji-engine` 仍是唯一确定性核心，Web/API 未复制评分常量或规则分支。
- Canonical Hash、Ruleset/Profile 版本、历史 Replay、Reanalysis 和比较语义不变。
- 私人表继续 FORCE RLS；API 从服务端会话取得身份，不信任前端 user id。
- DeepSeek 锁字段、确定性模板回退、无 Key 运行和 Provider 失败隔离保持不变。
- PC 优先、移动端五入口、图表文字替代、离线公共壳、Windows/Linux 视觉与 Hash 门禁继续保留。
- 失败 Run、视觉 diff artifact、Secret Scan、Gitleaks、许可证和文档链接门禁不得软失败。

## 合并门槛

远端必要 Job 必须 0 failed、0 skipped、无软失败；17 个 Hash、Ruleset、Golden、Snapshot 受保护值不得漂移。任何 P0、阻断 P1、私密数据泄漏、RLS 失败或无法解释的视觉变化都会令 `AUTO_MERGE_READY=false`。
