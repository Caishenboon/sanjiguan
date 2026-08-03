# 传统术数机械算法审计 v1

状态：Sprint 20A 审计稿；不改变业务输出。审计基线为 `dd5fddaa0b7edd017055f20c820277fbc3671632`。

## 结论先行

| 系统 | 当前真实完成度 | 本审计的判断 |
|---|---|---|
| 八字 | 历史法定时间、太阳时候选、节气瞬时和多 Profile 四柱机械候选 | 可重复的研究基座；日界、太阳时主盘和传统来源未冻结；不是完整八字论命 |
| 紫微 | 人工核验农历输入下的命身宫、十二宫、五行局、十四主星、候选四化和简化周期 | 可重复的有限三合结构候选；五项核心传统来源均为空，不得称完整三合或任何门派定法 |
| 易经 | 实物三钱六次录入、本卦、变卦、动爻、六十四卦结构 | 4096 状态穷举通过；不是完整六爻纳甲断卦，也没有多动爻断法 |

机器可审计清单见 [rule-audit-v1.json](./rule-audit-v1.json)，它逐条登记实现、代码位置、版本、来源、争议、测试和生产状态。校验命令：

```bash
python scripts/validate_traditional_method_audit.py
```

## 三层边界

1. `mechanical`：时间规范化、历法/天文候选、干支或宫星结构、投币与卦变。机械可重复不等于传统方法已审校。
2. `traditional_interpretation`：旺衰、用神、飞化论断、六爻纳甲断法等。未实现或未审校者保持 `DISABLED`。
3. `sanji_original`：六象及下游融合规则。必须标为三际观原创研究，不得反向充当传统来源。

## 现有边界与版本

- Calendar：`CALENDAR.MIGRATION.BASELINE.V1`，实现位于 `packages/sanji-engine/src/sanji_engine/calendar/`。
- BaZi：`BAZI.FOUR_PILLARS.MECHANICAL.RESEARCH.V1/1.0.0`，三套显式 Profile；禁止隐式默认。
- Ziwei：`ZIWEI.SANHE.MECHANICAL.RESEARCH.V1/1.0.0`，仅人工核验农历输入和两套闰月候选。
- Yijing：`YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1/1.0.0`，解释与吉凶字段为空。
- 公开入口仍经 `sanji_engine` 契约；本审计没有在页面、API 或 LLM 层复制算法。

## 测试证明什么

现有测试证明确定性、边界传播、Replay 和跨平台 Hash；它们不证明传统权威性或人生预测有效性。八字 74 个边界样例、易经 4096 状态、紫微机械参考输出均应归类为 `mechanical_reference`，不可命名为权威传统金样例。

## 主要发现

- P0：本轮未发现跨平台漂移、Replay 破坏、数据损坏或安全问题。
- P1：八字日柱 epoch 缺独立权威来源；D-002/D-003 未冻结；紫微五项核心来源为空且闰月、四化、周期存在方法争议；易经币面 2/3 约定缺正式来源登记。
- P2：八字传统解释和运势层、紫微高级结构、易经六爻纳甲均未实现；这些是诚实的范围缺口，不是本 Sprint 的实现任务。

详细分级见 [remediation-backlog-v1.md](./remediation-backlog-v1.md)。在项目所有者逐项批准 [profile-decision-v1.md](./profile-decision-v1.md) 前，不改变任何生产默认或规则激活状态。

## 不变性声明

本 Sprint 不修改 `sanji-engine` 业务实现、Ruleset、数据库迁移、Golden、Snapshot、评分、阈值或历史 Hash。新增测试只校验审计清单的结构和路径，不为任何流派背书。
