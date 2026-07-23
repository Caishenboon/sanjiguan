# PostgreSQL 16 RLS 权限矩阵

| 资源 | member（本人） | owner 管理角色 | viewer |
|---|---|---|---|
| profile 基础资料 | 读写 | 全部读写 | 仅显式 `profile:read` grant 可读 |
| evidence/chart/analysis | 本档案读写 | 全部读写 | 必须另有对应 scope；默认不可读 |
| relationship | 本档案读写 | 全部读写 | 仅显式 `relationship:read` 可读 |
| relationship consent | 本档案读写 | 全部读写 | 不可读写 |
| journal | 本档案读写 | 全部读写 | 默认不可读 |
| grant | 档案所有者管理 | 可管理 | 仅可查看授予自己的记录 |

`profile_grants` 与 `relationship_consents` 是独立概念。grant 包含状态、scope、
创建/到期/撤销时间和撤销者；撤销后 RLS 在下一条语句立即重新判定。

应用事务必须设置 `app.current_user_id` 与 `app.current_user_role`。应用角色为
`NOBYPASSRLS`、非表 owner，受保护表使用 `FORCE ROW LEVEL SECURITY`。
CI 通过 PostgreSQL 16 service 从空库迁移并以 `SET ROLE app_runtime` 验证。
