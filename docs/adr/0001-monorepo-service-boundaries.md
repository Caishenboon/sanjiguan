# ADR-0001：模块化 monorepo 与服务边界

- 状态：Accepted
- 日期：2026-07-23

## 决策

采用 monorepo：`apps/web` 为 Next.js 展示层，`apps/api` 为 FastAPI 与后台任务入口，`packages/engine` 只容纳确定性计算，`packages/rules` 保存带版本与来源的规则，`packages/prompts` 保存受约束提示模板。

浏览器只访问 `/api/v1`，不得直接访问 LLM、数据库或对象存储。可视化只消费结构化 API 数据。

## 后果

前后端可独立部署；规则与模型解释可分别测试、回放和停用。Sprint 0 仅创建边界与契约，不创建完整产品。
