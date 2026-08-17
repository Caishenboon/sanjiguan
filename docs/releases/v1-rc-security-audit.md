# V1 RC 安全与隐私验收

## 已验证边界

- 邀请令牌与会话令牌仅以 SHA-256 哈希持久化；一次性邀请兑换后不能复用。
- Owner、Member、Viewer 由服务端鉴权；传统管理员路由 Owner-only，Member 仅能写入本人主体。
- PostgreSQL 私人表启用并强制 RLS，应用角色无超级用户、建库、建角色及 BYPASSRLS 权限。
- POST/PATCH/DELETE 使用 24 小时 Idempotency-Key，绑定用户、路由和请求指纹；冲突返回 409。
- 生产配置拒绝 HTTP、缺失/弱加密配置和不安全 Cookie；Cookie 为 HttpOnly、SameSite=Strict。
- 修改请求校验 Origin；私人响应 `Cache-Control: no-store`；PWA 不缓存私人/API路径。
- 日志只记录关联ID、方法、路由、状态和耗时，不记录请求正文、梦境、关系或出生资料。
- DeepSeek 密钥只允许环境变量；核心、Hash和测试不依赖 Provider。
- 导出不含密钥、Session、加密材料或其他用户数据；彻底删除会明确使部分 Replay 不可用。

## 本轮发现并修复

1. Profile PATCH 原先只更新称谓且会忽略出生修改：改为按字段动态更新并加密保存完整原始记录。
2. 产品表单曾用 `0,0` 补造经纬度、三钱曾预填：改为显式用户输入，缺失时阻止提交。
3. 管理员研究端点曾在接线中被误放宽：恢复 Owner-only，并建立独立主体范围用户端点。
4. 传统完整运行表原 RLS 只允许 Owner：新增只允许 Owner/Member 本人记录、明确排除 Viewer 的策略。
5. 邀请接受缺少安全签发产品入口：新增 Security Definer 签发函数，API只传入令牌哈希。
6. 恢复脚本错误要求原始记录具有分析 Hash：改为只校验派生条目，恢复演练重新通过。

## 仍需运营决策

- 公开前完成产品负责人书面许可决定与最终全历史人工复核。
- 生产 KMS、备份外部加密、保留期限、数据地区和删除 SLA 仍需部署环境确认。
- Viewer 资源级授权生命周期沿用既有表与门禁；上线前应以实际运营角色做一次人工撤权演练。
- 真实 DeepSeek Smoke 不是普通 CI 门禁；仅在产品负责人明确触发时执行虚构输入调用。
