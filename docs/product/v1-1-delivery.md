# 三际观 V1.1 产品质量交付

三际观是一套融合传统术数、宿世因缘结构与生命轨迹观照的确定性推演系统。三际枢负责计算、取证、合参和成断；DeepSeek 仅可把既定结构写成文辞。

## 本轮完成

- 首页、立卷、记录、合参、三际录、报告和专题页面统一了普通用户语言与阅读层级。
- 手机固定为首页、三际录、合参、断章、更多五个入口；深层页面增加明确返回路径。
- 统一象势、证契完备度、证契、逆证、相争和不成断表达；研究细节仍可查阅但不压在首屏。
- Web 请求增加超时、取消、请求关联 ID 和安全错误；API 错误保持向后兼容并避免正文泄漏。
- PWA 只缓存公开离线壳；私人路由 network-only，升级时清理旧壳并提示用户刷新。
- 增加全局加载、错误、离线状态以及 CSP、frame、referrer、permissions 安全头。
- 没有新增 migration：现有索引和 FORCE RLS 能覆盖本轮路径，缺少可证明的新索引需求。

## 不在本轮

八字、紫微、易经、六象、宿世、中阴、缘契、命势、K 线、吉凶、应期、权重、阈值和 Ruleset 均未修改。未调用 DeepSeek；没有生产激活、公开仓库、Tag、Release 或许可证决定。

## 验收入口

- 红蓝审计：[v1-1-comprehensive-red-blue-audit.md](v1-1-comprehensive-red-blue-audit.md)
- 用户指南：[../user-guide.md](../user-guide.md)
- 测试说明：[../testing/v1-1-quality.md](../testing/v1-1-quality.md)
- 视觉证据：[evidence/manifest.json](evidence/manifest.json)
- 交接状态：[../handoff/current-state.md](../handoff/current-state.md)

最终远端 Commit、PR、CI、Merge SHA 与 main 复验只在真实发生后写入交付证据；文档不预填虚假成功。
