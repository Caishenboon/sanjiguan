# 历史交付索引

| 阶段 | PR | Merge SHA / 状态 | CI Run | 主要功能 | 关键文档 | 规则版本/结果 | 后续状态 |
|---|---:|---|---:|---|---|---|---|
| Sprint 0–3 | #1–#6 | 已合并 | 见各 PR | 工程、安全、知识工坊、首个闭环 | `docs/sprints/` | 研究基线 | 部分被核心迁移取代 |
| 三际枢边界 | #7 | `726277a6…` | 见 PR | 独立核心、契约、Replay 地基 | `docs/sprints/sanji-engine-core-boundary-foundation.md` | Core API 1.0 | 当前有效 |
| Signals/Inference | #8 | `359e26a1…` | 见 PR | 30 案例等价迁移 | `docs/sprints/signals-inference-equivalence.md` | Hash 保持 | 当前兼容基线 |
| 易经三钱 | #9 | `4efc9d70…` | 见 PR | 4096 机械状态 | `docs/sprints/yijing-three-coin-mechanical.md` | 机械研究 | 当前有效 |
| 八字/紫微地基 | #10–#12 | 已合并 | 见各 PR | 四柱、紫微机械与 Oracle 对照 | `docs/architecture/` | 多 Profile | 当前有效 |
| 视觉确定性 | #13 | `3e3fc536…` | 见 PR | 双平台 Snapshot 与失败 Artifact | `docs/testing/visual-regression.md` | 不改算法 | 当前有效 |
| 六象到 V1 闭环 | #14–#19 | 已合并 | 见各 PR | 产品主干、证据、专题、命势、部署收口 | `docs/sprints/`、`docs/releases/` | 三际原创研究 | 当前有效 |
| 方法审计 | #20 | `45282727…` | `30786926806` | 传统机械审计与 Profile 草案 | `docs/methods/traditional-method-audit-v1.md` | 不改业务结果 | 被后续可信基线扩充 |
| 八字/易经可信基线 | #21 | `0c9d05a6…` | 见 PR | 日柱来源、边界 Profile、钱面契约 | `docs/methods/bazi-yijing-mechanical-trust-v1.md` | 新 reference，旧 Hash 保持 | 当前有效 |
| 紫微可信基线 | #22 | `0f24751e…` | `30797815287` | 受限双 Profile 与机械 reference | `docs/methods/ziwei-mechanical-trust-v1.md` | `sha256:97d96f…` | 当前有效 |
| 八字传统结构 | #23 | `bb8bcbd7…` | `30802736516` | 藏干、十神、干支关系 | `docs/methods/bazi-traditional-structure-foundation-v1.md` | 结构研究 | 当前有效 |
| 固定上游对照 | #24 | 由 #25 一并进入主干 | `30812620050` | 固定上游适配与对照 | `docs/methods/upstream-traditional-engines-v1.md` | 不作多数投票 | 被 #25 集成 |
| 传统算法 V1 | #25 | `2a1e8fb7…` | `30826916968` | 八字、受限三合紫微、京房纳甲六爻 | `docs/methods/traditional-algorithms-complete-v1.md` | 全部研究态 | 当前主干基线 |
| V1 RC 封卷 | #26 | `bef14661…` | 见 PR/main | 邀请、完整旅程、部署恢复、交接和公开整备 | `docs/releases/v1-rc-delivery.md` | 不改旧 Hash | 当前主干基线 |
| V1.1 产品质量 | 待创建 | Open（预期） | 待远程运行 | 语言、旅程、错误边界、PWA 隐私与安全头 | `docs/product/v1-1-delivery.md` | 不改算法与旧 Hash | 本轮施工 |

省略的完整 SHA 可由 Git 历史核验；本表不保存密钥、私人数据、本机路径或外部数据正文。
