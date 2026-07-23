# Sprint 1A.6 运行证据与契约收口

Sprint 1A.5/1A.6 工程验收闭环所需的真实数据库与 HTTP 证据已经取得。

## 真实运行

- PostgreSQL 16.14
- 本地证据 run ID：`local-pg16-919ec741-5e6b-4842-9df9-e2620c95cb47`
- 源码快照 SHA-256：`68a5c07e2367c0a6cbad14a592d8b78c13786853a2a7dcc9f2aee45cd135be00`
- migration 0001–0006 从空库成功；第二次执行零变更
- PostgreSQL 集成：5/5 通过
- HTTP→PostgreSQL E2E：1/1 通过
- 测试数据清理：残留 users=0

当前仓库没有 commit 或 remote，因此没有可提供的 CI run ID、commit SHA 或运行
链接；已按指令保存等价、可复现的本地完整日志。

## 汇总

- Python 普通测试：44 passed
- PostgreSQL：5 passed
- API memory：4 passed
- API PostgreSQL E2E：1 passed
- 总 test methods：54 passed，0 failed，0 skipped
- Web production build：通过
- 静态门禁：8 passed

断语 provenance、人工覆盖审计、LLM allowlist、排名唯一性、同意撤回和匿名事件
约束均已闭环。

Sprint 1B 结论：不可全面开工；D-002、D-003、D-005 等阻断项仍未解决。所有术数
生产规则继续关闭，未接入 DeepSeek。
