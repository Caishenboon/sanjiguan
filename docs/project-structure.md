# 项目目录与责任边界

```text
apps/web/                 Next.js 展示层；禁止供应商密钥与确定性计算
apps/api/                 FastAPI、鉴权、任务编排、LLM Gateway
packages/engine/          纯确定性计算模块；当前仅目录占位
packages/rules/           JSON Schema、draft manifest、未来版本规则
packages/prompts/         受约束解释模板；不能覆盖计算结果
packages/shared-types/    跨服务契约
knowledge/                来源清单、审核区、摄入暂存
infra/migrations/         PostgreSQL/pgvector/RLS 迁移草案
infra/docker/             本地/部署容器配置（后续）
infra/monitoring/         脱敏、指标与告警配置（后续）
docs/adr/                 架构决策记录
docs/api/                 OpenAPI 草案
docs/security/            威胁模型与密钥运行约定
docs/plans/               Sprint 实施与验收
tests/golden/             已编号的金样例输入与未来权威期望
tests/security/           安全测试（后续扩展）
```

空引擎目录是有意的：方法未确认前不放置“临时算法”，避免占位实现被误激活。
