# 项目目录与责任边界

```text
apps/web/                 Next.js Web/PWA；展示、输入与渐进披露
apps/api/                 FastAPI、鉴权、编排、持久化与受控 LLM Gateway
packages/sanji-engine/    三际枢；唯一确定性算法核心与版本化契约
packages/sanji-ui/        共享设计系统与 Storybook
packages/oracle-adapters/ 仅用于固定独立对照，不进入正式证据
packages/upstream-adapters/固定上游传统算法适配
packages/rules/           通用规则 Schema 与门禁资产
prompts/                  受控成文模板；不能覆盖核心结论
packages/shared-types/    跨层契约
knowledge/                来源、授权、审核与 restricted/sealed 边界
infra/migrations/         只追加的 PostgreSQL migration 与 FORCE RLS
infra/backup/             备份说明与运维资产
docs/                     ADR、方法、API、安全、交接和发布证据
tests/                    单元、集成、安全、契约与历史 Hash 门禁
```

三际枢公开入口仅为 `sanji_engine.public` 的 `validate_request`、`execute`、`replay` 和
`inspect_ruleset`。Web、API 和 DeepSeek 层不得复制算法、评分常量或规则分支。

当前阶段和机器可读路径以 [`handoff/project-manifest.json`](handoff/project-manifest.json)
为准；早期“空引擎目录”描述已经被三际枢独立核心方案取代。
