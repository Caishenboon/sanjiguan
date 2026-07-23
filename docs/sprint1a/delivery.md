# Sprint 1A 交付说明

## 已完成

- FastAPI/Next.js/PostgreSQL migration 的 monorepo 骨架。
- 邀请制认证、安全 Cookie、档案 CRUD、POST/PATCH/DELETE 幂等语义。
- 原始出生信息、历史时区、地点/经纬度、精度和用户确认字段。
- 法定时间、地方平太阳时、地方视太阳时、校正审计链和候选区间。
- 节气瞬时基础组件；不产生完整八字结论。
- evidence、analysis run、规则版本、审计事件、viewer grant 与关系同意数据表。
- 应用层 UUIDv7、FORCE RLS、非 owner/NOBYPASSRLS 角色契约。
- JSON Schema、可执行 OpenAPI 导出及同步门禁。
- 时区、DST、日期变更线、节气边界、未知时间、RLS 与幂等测试。

## 明确未实现

所有用户列明的禁止项均未实现。八字、紫微、易经和密宗规则清单仍为
`draft + disabled + UNCONFIRMED`；高修行/大愿型和财富维度默认关闭；
DeepSeek 不调用。

## 验收命令

见仓库根目录 `README.md`。`scripts/validate_sprint1a.py` 同时检查规则门禁、
敏感环境变量、禁止目录和 OpenAPI 漂移。

## 已知限制

本轮 API 使用进程内存适配器，以便无需生产平台决定即可运行。数据库迁移与 RLS
是 PostgreSQL 契约，但真正的持久化 repository、迁移运行和跨进程会话需在后续
工程 Sprint 完成；不得将内存适配器部署为生产服务。
