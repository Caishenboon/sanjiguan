# Sprint 17：宿世观、中阴观、缘契观

本 Sprint 增加共享确定性专题证据图、认识状态、确定性命名规则、三类专题候选、加密持久化、三际录、Replay、Reanalysis 和版本差异比较。所有功能均为 `sanji_original / research_active / UNCONFIRMED`，不可生产激活。

## 资产与版本

- Topic Ruleset：`topic-research-rules/1.0.0`
- Naming Ruleset：`past-life-name-rules/1.0.0`
- Evidence Policy：`liuxiang-user-evidence-policy/1.0.0`
- Engine Bundle：`topic-research-v1.0.0`
- 合成一致性案例：72 个，宿世/中阴/缘契各 24 个
- 聚合哈希：`sha256:695d404fee8a31d484661ed8617ee3bd96d6ae5d48f77d9be3fc13a93d614772`

案例只证明确定性、状态机、同源去重、命名稳定、Replay 与跨平台哈希，不证明现实有效性。

完全虚构 UI 审核图：

- [宿世观桌面端](../screenshots/sprint17-sushe-desktop.png)
- [宿世观移动端](../screenshots/sprint17-sushe-mobile.png)

## API 摘要

- `GET /api/v1/profiles/{profile_id}/topics/{topic_type}/evidence`
- `POST /api/v1/profiles/{profile_id}/topics/{topic_type}/executions`
- `GET /api/v1/topic-executions/{execution_id}`
- `POST /api/v1/topic-executions/{execution_id}/replay`
- `POST /api/v1/topic-executions/{execution_id}/reanalyze`
- `POST /api/v1/topic-executions/compare`

API 只协调授权、加密和持久化，所有候选、姓名、分数与状态均来自 `sanji-engine` 的四个公开入口。

## 隐私与同意

梦境正文、关系正文、日记正文和完整出生资料不进入图、Trace 或日志。单方关系仅能输出“基于单方记录的缘契观察”；只有有效双方合参同意才能形成双向结构。同意撤销后的记录不参与新执行。

## 未实现

未实现历史人物真实资料匹配、命势长图、人生 K 线、最终三际断章、DeepSeek 正式成文、无条件未来事件预测、权重训练、图数据库、新微服务或生产激活。
