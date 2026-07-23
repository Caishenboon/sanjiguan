# Sprint 1A.5 交付说明

## 完成项

- 产品名称、题辞、术语表、语言规范与 ADR。
- 首页、三际录、六象合参、三际断章及其余命名页面的基础信息架构。
- 结构化断语、报告章节、应期、证契四个 JSON Schema 和 Demo fixture。
- PostgreSQL 16 repository、连接池、事务、超时、错误边界与有序 migration 执行器。
- 生产环境内存适配器拒绝启动；AES-GCM 测试 key provider 也被生产门禁拒绝。
- viewer resource grant、撤权和关系同意生命周期 migration。
- PostgreSQL 16 CI service：空库迁移、重复迁移/漂移、RLS、角色、跨用户、
  viewer 撤权、关系同意、回滚及并发幂等测试。
- 品牌语言、Schema、secret、受阻算法和 OpenAPI 静态门禁。

## 验证结果（由 Sprint 1A.6 收口）

本节原有的 41/42 与 PostgreSQL skipped 记录是阶段性结果，现已由 Sprint 1A.6
统一统计替代：普通 Python 44、PostgreSQL 5、内存 API 4、PostgreSQL E2E 1，
合计 54 个 test method 通过，0 failed、0 skipped。真实 PostgreSQL 16.14
证据见 `outputs/postgres16-evidence.json`。

## 明确未实现

所有 D-002、D-003、D-005 阻断算法及用户列明禁止项均未实现。规则 manifest
仍为 `draft + disabled + UNCONFIRMED`，DeepSeek 未调用。

## 已知工程边界

PostgreSQL repository 和真实数据库验证契约已交付；现有 HTTP API 的快速演示
路径仍使用内存 store，且生产环境会硬失败，避免误部署。将全部认证/CRUD HTTP
路径切换到 PostgreSQL repository 需要先配置生产 KMS/认证数据库角色，不得用
测试 key provider 冒充生产安全。
