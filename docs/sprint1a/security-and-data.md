# Sprint 1A 安全与数据契约

- 邀请一次性使用；无公开注册。会话使用服务端令牌摘要和
  `Secure + HttpOnly + SameSite=Strict` Cookie。
- 写接口要求 16–128 字符 `Idempotency-Key`。记录绑定用户、HTTP 路由和规范化
  请求指纹，保留 24 小时；同键同请求重放原状态码与响应，同键异请求返回 409。
  POST、PATCH、DELETE 均适用。
- UUIDv7 由应用层生成。
- PostgreSQL 应用角色不是表所有者且为 `NOBYPASSRLS`；受保护表启用并强制
  RLS。owner/member 为最小访问面；`profile_grants` 已建模，viewer 产品开关保持关闭。
- 关系同意记录包含版本、记录时间、状态、撤回时间和证明类型。
- DeepSeek 仅保留空环境变量与配置接口，不调用模型，不保存真实密钥。
- 规则缺少来源、复核者或金样例时不可由 `draft` 晋升。密宗审校人不得由 Codex、
  LLM 或无传承资格的普通审核者代替；未找到审校人不阻塞无关工程底座。

迁移中的策略是安全契约；当前 API 的内存适配器仅用于本地演示和单元测试，
不能视作生产持久化实现。
