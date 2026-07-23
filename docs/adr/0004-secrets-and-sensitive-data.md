# ADR-0004：敏感数据与密钥管理

- 状态：Accepted
- 日期：2026-07-23

## 决策

DeepSeek 仅由后端 Gateway 通过 `DEEPSEEK_API_KEY` 读取；Secret Manager 是生产唯一来源。密钥不进入前端、数据库、日志、追踪、导出、镜像层或 Git。

出生、地点、梦境、关系、日志和输入快照使用应用层 envelope encryption；传输使用 TLS；数据库不暴露公网；访问由 RLS 和最小权限共同限制。日志只记录 request ID、稳定错误码和脱敏元数据。

旧密钥已暴露，吊销是上线前人工阻断项，仓库不能代为完成控制台操作。
