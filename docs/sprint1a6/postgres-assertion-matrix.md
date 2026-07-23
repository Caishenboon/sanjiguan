# PostgreSQL 16 断言覆盖矩阵

| # | 必须证明的断言 | 运行测试 |
|---|---|---|
| 1 | 空库执行全部 migration | `run_postgres_evidence.py` 首次迁移 |
| 2 | 第二次迁移无重复结构 | 同脚本第二次迁移输出为空 |
| 3 | 非法 schema 漂移被拒绝 | `test_migration_drift_is_rejected` |
| 4–6 | runtime 非 owner、无 BYPASSRLS、FORCE RLS | `test_runtime_role_and_force_rls` |
| 7 | Member A 不能读写 Member B | `test_member_isolation_owner_and_viewer_revocation`、HTTP E2E |
| 8 | Owner policy | `test_member_isolation_owner_and_viewer_revocation` |
| 9–11 | Viewer 显式资源、只读、撤权立即失效 | 同上 |
| 12 | 同意撤回后拒绝双人分析 | `test_transaction_rollback_and_consent_withdrawal` |
| 13 | 匿名事件拒绝可识别字段 | 同上，数据库 CHECK |
| 14 | 同键同指纹一次写入 | `test_concurrent_idempotency_single_write_and_user_scope`、HTTP E2E |
| 15 | 同键异指纹 409 | HTTP `test_auth_crud_isolation_idempotency_logout_and_soft_delete` |
| 16 | 并发仅一次业务写入 | `test_concurrent_idempotency_single_write_and_user_scope` 验证 evidence count=1 |
| 17 | 事务失败回滚 | `test_transaction_rollback_and_consent_withdrawal` |
| 18 | 测试数据清除 | 两套测试 `tearDownClass` + evidence 中 residual users=0 |

HTTP E2E 还覆盖邀请、会话、创建/读取/修改三际录、跨用户 404、幂等重放、
软删除后 404、注销后 401，并直接查询数据库确认软删除记录。
