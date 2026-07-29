# Sprint 16 交付说明

本 Sprint 将授权用户记录经六类证据政策接入既有 Signal v2 与唯一
Liuxiang Inference，并将执行历史和三际录迁移到 PostgreSQL 权威存储。

- 新规则束：`liuxiang-evidence-research-v1.0.0`
- 状态：`sanji_original / research_active / UNCONFIRMED`
- 生产激活：`false`
- 新合成案例：72，资产级别 `synthetic_conformance`
- 72 案例聚合 Hash：`sha256:250e06cce33d5da5d66570386921ab3dc35df403f0c5c514bbb128f3b1051059`
- 数据库迁移：`0016_liuxiang_evidence_archive_v1.sql`
- API 契约：`docs/api/liuxiang-archive.openapi.json`
- 详细架构：[`../architecture/liuxiang-evidence-archive-v1.md`](../architecture/liuxiang-evidence-archive-v1.md)

界面审查（完全虚构数据）：

- [六象研究桌面端](../screenshots/sprint16-liuxiang-desktop.png)
- [三际录移动端](../screenshots/sprint16-chronicle-mobile.png)

未实现：解释性八字/紫微/易经映射、宿世、中阴、最终缘契、命势长图、最终
吉凶与应期、DeepSeek 成文、Oracle/LLM/向量证据、生产激活。
