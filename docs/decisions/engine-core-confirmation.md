# E-001 至 E-012 冻结记录

产品负责人于 2026-07-23 接受并冻结 E-001 至 E-012。工程解释以
ADR-0007 为准。

| ID | 已冻结决定 |
|---|---|
| E-001 | `packages/sanji-engine` 与 import `sanji_engine` |
| E-002 | 首版继续 Python，不跨语言重写 |
| E-003 | Python `>=3.11` |
| E-004 | 评分禁用二进制浮点；整数基点优先，Decimal 显式精度/舍入，固定完整 tie-breaker |
| E-005 | RFC 8785 JCS 兼容 Canonical JSON；哈希细节版本化且禁止静默变更 |
| E-006 | Engine API 1.0 仅四个公开入口 |
| E-007 | 正式规则状态机及 `revoked_for_future_runs` |
| E-008 | Calendar 首迁并逐字段、Trace、哈希等价验证 |
| E-009 | Signals/Inference 仅冻结为 `research_baseline` |
| E-010 | 仅建立 manifest 设计/草案，不迁生产历史、不伪造 manifest |
| E-011 | 十二项条件满足后方可拆仓；当前不建第二仓库 |
| E-012 | 代码、规则、知识、测试许可分治且未定；仓库保持 Private |

以上冻结不代表术数正确性、流派确认、权重认可或生产激活。
