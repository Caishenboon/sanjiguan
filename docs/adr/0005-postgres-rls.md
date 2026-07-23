# ADR-0005：PostgreSQL、pgvector、UUIDv7 与 RLS

- 状态：Proposed
- 日期：2026-07-23

## 决策

依规格书采用 PostgreSQL 16 与 pgvector；业务主键使用 UUIDv7；时间使用 `timestamptz`；按 `owner_id/profile_id/analysis_run_id/created_at` 建索引；用户数据启用 RLS。

## 尚待确认

部署平台对 UUIDv7 的原生支持、应用会话向 PostgreSQL 传递主体 ID 的机制、向量维度与 embedding 模型需在部署/模型选型后冻结。
