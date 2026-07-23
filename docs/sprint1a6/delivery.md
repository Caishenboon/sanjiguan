# Sprint 1A.6 交付说明

## 运行证据

由于当前 Git 仓库没有 commit 和 remote，不能生成 GitHub Actions run ID、commit
SHA 或链接。本轮采用指令允许的等价本地证据：

- workflow：`Local PostgreSQL 16 Sprint 1A.6 Evidence`
- run ID：`local-pg16-919ec741-5e6b-4842-9df9-e2620c95cb47`
- 源码快照 SHA-256：`68a5c07e2367c0a6cbad14a592d8b78c13786853a2a7dcc9f2aee45cd135be00`
- 时间：2026-07-23 09:47:29–09:47:35 UTC
- PostgreSQL：16.14，官方 Windows x86-64 binary archive
- 空库 migration：0001–0006 全部成功
- 第二次 migration：零变更
- PostgreSQL 集成：5 passed / 0 failed / 0 skipped
- HTTP→PostgreSQL E2E：1 passed / 0 failed / 0 skipped
- 测试结束残留 users：0

机器证据为 `outputs/postgres16-evidence.json`，完整 stdout/stderr 为
`outputs/postgres16-evidence.log`。可用 `POSTGRES_ADMIN_URL=... python
scripts/run_postgres_evidence.py` 在隔离数据库 `sanjiguan_evidence` 重现。

## 契约收口

- HTTP 测试模式必须显式声明 `APP_ENV=test`、`STORAGE_BACKEND=postgres`、
  `KEY_PROVIDER=test-only`；不声明 backend 不回退内存。
- 生产环境拒绝 memory 和 test-only key provider。
- 断语来源拆为 verdict/prose/review provenance；人工覆盖强制审核人与审计链。
- LLM fixture 只能经 allowlist 合并五类文字字段，不能提交整个对象或改写锁定字段。
- 同一 analysis run + subject 的 rank 由数据库唯一约束保证。
- 同意撤回由数据库 trigger 阻止新的双人分析；匿名事件由 CHECK 禁止对方标识字段。

## 统一测试统计

普通 Python 44、PostgreSQL 5、内存 API 4、PostgreSQL HTTP E2E 1，合计
54 个 test method 全部通过；skipped=0、failed=0。Web production build 1 次通过，
静态门禁 8 项通过。早先 41/42 差异来自其间新增一个 encryption provider 测试；
本轮改为分类运行，不把 skipped 计入 passed。

## Sprint 1B 结论

**不可全面开工。** D-002、D-003、D-005 及其人工流派审校仍阻断任何相关生产
术数规则；D-010、D-012 等仍阻断生产部署。只可继续不依赖这些决策的工程维护。
所有规则继续 `draft + disabled + UNCONFIRMED`，DeepSeek 未接入。
