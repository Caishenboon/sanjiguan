# ADR-0012：紫微研究引擎、差分 Oracle 与 Sanji UI 平台边界

- 状态：Accepted for research
- 日期：2026-07-27
- 决策依据：D-004 已冻结；D-005 仍未冻结

## 决策

1. 紫微首版仅实现受限三合基础排盘的机械结构，并以显式 Profile
   区分闰月等争议方法。所有 Profile 均保持
   `research_active + UNCONFIRMED + production_activatable=false`。
2. Engine 只接受用户已核验的农历字段与显式时辰索引。本 Sprint
   不将公历自动换算为农历，也不静默选择闰月或子时规则。
3. lunar-python、tyme4py、sxtwl 与 iztro 只作为隔离的差分 Oracle。
   Oracle 输出不得进入 Engine 哈希、规则状态、排名或锁定判断，也不得
   被提升为传统权威。
4. `packages/sanji-ui` 是应用层共享视觉与研究状态组件边界。页面不得
   复制 Engine 算法、规则常量或 Oracle 判断。
5. PostgreSQL 仅以加法迁移保存 owner-scoped 的研究运行与差分摘要；
   旧记录不回填，不伪造 replay manifest。

## 原因

D-005 的四化、闰月、子时与权威金样例仍待产品负责人及合格审校人
确认。显式 Profile 和差分 Oracle 能暴露方法差异，同时避免把第三方
库或工程假设误当作生产规则。统一 UI 契约则使研究状态、来源、版本、
Trace 和哈希在所有页面上保持可见。

## 后果与门禁

- 紫微结果只能标为研究机械排盘，不得生成性格、吉凶、宿世或修行解释。
- 任一 source claim 未审校、Profile 仍含 `UNCONFIRMED` 或权威金样例
  不足时，不得晋升 `production_active`。
- Oracle 缺失、失败或结果不同都必须结构化呈现，不能静默回退为 Engine
  结论。
- 未来更换第三方版本必须更新 lock、notice、差分基线与评估记录。
- 代码、规则数据、知识内容和测试数据许可分别治理；本 ADR 不选择许可证，
  不改变私有仓库可见性。
