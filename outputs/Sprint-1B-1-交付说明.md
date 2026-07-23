# Sprint 1B-1 交付说明

## 交付结论

本阶段实现“三际录与六象证据采集”的独立工程基础。系统可保存八步引导进度、
加密证据、修行日志、关系同意、资料完整度、记录可靠性、时间线和实物三钱原始结果。
所有结果均停留在资料记录层，不输出术数解释、宿世身份或中阴类型。

## 核心交付

- PostgreSQL 迁移 `0007_sprint1b1_evidence_foundation.sql`。
- Evidence、Onboarding、Journal、Relationship Consent、Physical Three-Coin API。
- Evidence 与 Three-Coin JSON Schema，以及独立 OpenAPI 契约。
- About、个人档案首页及八步断点续填界面。
- 应用层加密、FORCE RLS、成员隔离、24 小时幂等和匿名关系资料最小化。
- 记录可靠性与资料完整度纯函数；均附带“非术数评分”语义。
- 单元、PostgreSQL 16、HTTP→PostgreSQL、Web Build、静态门禁与 Secret Scan。

## 未激活边界

未实现八字、紫微、自动宿世本卦、宿世身份评分、中阴评分、高修行/大愿型、
名人匹配、K 线、DeepSeek、Embedding、RAG 或任何 LLM 补算。

## 验收证据

本地从空库连续应用 0001–0007 并重复迁移；PostgreSQL RLS 集成测试与 HTTP E2E
均实际运行。机器可读统计见 `sprint1b1-test-summary.json`。最终 GitHub Actions
run 与 PR 链接在 CI 完成后补入交付报告。

## Sprint 1B-2 前置阻断

D-002、D-003、D-005、D-010、D-012 仍未冻结；本阶段没有绕过这些决策。
下一 Sprint 必须由产品负责人另行下达指令。
