# 八字传统结构基础 v1

状态：`research_active / UNCONFIRMED / production_activatable=false`

本能力只检测传统结构事实，不等于完整八字论命。它不输出旺衰、旺相休囚死、格局、调候、喜忌、用神、大运、流年、流月、合化、成局、吉凶或应期。

## 分层与版本

链路固定为：四柱机械层 → 八字传统结构层 → 未来传统解释层 → 三际观原创研究层。本轮只实现第二层。

- 输入四柱：`BAZI.FOUR_PILLARS.MECHANICAL.RESEARCH.V1 / 1.0.0`
- 结构方法：`BAZI.TRADITIONAL_STRUCTURE.RESEARCH.V1 / 1.0.0`
- Ruleset：`bazi-traditional-structure-research-1.0.0`
- 主 Profile：`bazi-traditional-structure-research-v1 / 1.0.0`
- 资产版本：`bazi-traditional-structure-assets/1.0.0`

结构操作必须显式提供四柱候选 ID、原四柱 Ruleset/方法版本及藏干 Profile。它不重算出生时间，不覆盖旧四柱输出；历史四柱报告只有在显式新分析时才会生成结构结果。

## 藏干

十二支均返回有序藏干。当前并列两个候选 Profile：

- `hidden-stems-primary-secondary-residual-candidate-v1`：使用本气、中气、余气标签；不赋百分比或强弱。
- `hidden-stems-lunar-python-order-comparison-v1`：固定为 lunar-python 1.4.8 的对照顺序。

两个 Profile 在巳支次序上不同：前者为丙、戊、庚，后者为丙、庚、戊。系统不设隐藏默认、不判断哪一个是唯一正统；该差异标记为 `DISPUTED`，待合格传统来源与审校闭环。

## 十神

十神仅由日干与目标天干的五行生克及阴阳同异确定。日主与目标干角色固定，位置不会改变同一干对的十神关系。年、月、时干以及所有藏干均可计算；日干对自身返回比肩。

十干 × 十干的 100 个组合已逐项与 lunar-python 1.4.8 的独立实现对照一致。该对照证明工程表/公式一致性，不构成传统权威签署。

## 月令

月令只记录当前四柱候选的月支、可用节令上下文和节气边界敏感标记。`strength_conclusion`、`pattern_conclusion` 和 `useful_god_conclusion` 固定为空，不得由页面或 API 补算。

## 天干关系

检测同干、相生、相克和天干五合候选，并保留参与干、柱位和方向。检测五合不等于合化；本版本不判断合化元素、争合、月令成化或吉凶。

## 地支关系

检测同支、六合、六冲、六害、六破、子卯刑候选、自刑候选、寅巳申/丑未戌三刑候选、三合、三会和部分组合。完整三支只表示成员齐全，不表示成局。

以下继续显式争议：六破表、刑的范围、自刑范围、半合/拱合等部分组合。它们分别标记为 `DISPUTED` 或 `SCHOOL_SPECIFIC`，不得推导强弱、解冲、吉凶或人生事件。

## Reference 与来源状态

Reference 文件为 `traditional-structure-mechanical-reference-v1.json`，共声明 166 个 `mechanical_reference` 案例：12 藏干、100 十神、5 天干五合、31 地支成对关系、10 三支组合、8 个攻击与边界案例。

- 独立工程对照：lunar-python 1.4.8，MIT，仅用于藏干与十神。它不是传统权威，也不应被重复计作人工审校。
- 传统来源：仍标记 `TRADITIONAL_SOURCE_ATTESTATION_PENDING / UNCONFIRMED`。本轮没有用博客、营销内容或 AI 输出补齐来源。
- 新 Reference 聚合 Hash：`sha256:a81019a737762808cb29636b06753cbcf18582d968be107df428287f7463f25b`。

## Trace、Replay 与排序

Trace 记录来源四柱 Ruleset/方法版本、结构 Profile、藏干 Profile、查表、十神推导和关系检测。柱位顺序固定为年、月、日、时；关系类型有固定排序键；输入对象键序变化不改变输出与 Hash。未知时辰保留 `hour_pillar` 缺失，不补造时柱或相关结构。

原四柱 Ruleset、Golden、Reference 和 Hash 均不改写。结构新执行可按同一版本 Replay；升级规则须新建版本，不能静默重算历史归档。

## API 与最小展示

Owner 研究 API：`POST /api/v1/admin/research/bazi-four-pillars/structure`。API 只组装 Engine 请求，不计算十神或关系。现有八字研究预览在用户明确点击后展示 Profile、研究状态、藏干、十神、月令、关系、争议和未实现能力，并持续显示：“传统结构研究结果，不等于完整八字论命。”

## 后续门禁

进入任何传统解释 Sprint 前，必须完成合格传统来源、方法 Profile 和人工审校签署。本结构结果不得直接进入六象、宿世、中阴、缘契、命势、K 线、吉凶、应期或三际断章。
