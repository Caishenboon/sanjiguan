# 紫微机械可信基线 v1

本交付只冻结“当前代码怎样运行、怎样复现、争议在哪里”。它不是完整紫微斗数，不批准任何门派解释，也不把外部软件多数票当作传统权威。

## 当前代码事实

入口为 `packages/sanji-engine/src/sanji_engine/ziwei/mechanical.py::calculate_chart`，方法为 `ZIWEI.SANHE.MECHANICAL.RESEARCH.V1/1.0.0`，Ruleset 为 `ziwei-sanhe-research-1.0.0`。

| 能力 | 当前状态 | 当前实现 |
|---|---|---|
| 公历转农历 | NOT_IMPLEMENTED | 仅接收 `manual_verified_lunar_input`；不猜测转换 |
| 闰月 | DISPUTED | `LEAP_SAME_MONTH` 与 `LEAP_SPLIT_15` 并列，无默认 |
| 命宫、身宫 | IMPLEMENTED / UNCONFIRMED | 月数、时支候选公式 |
| 十二宫与宫干 | IMPLEMENTED / UNCONFIRMED | 固定逆排宫序与五虎遁候选 |
| 五行局 | IMPLEMENTED / UNCONFIRMED | 命宫干支纳音候选表 |
| 紫微定位与十四主星 | IMPLEMENTED / UNCONFIRMED | 局数、日数及两组星系偏移表 |
| 辅星、煞星 | NOT_IMPLEMENTED | `approved_auxiliary_stars=[]` |
| 生年四化 | IMPLEMENTED / DISPUTED | 只展示未审校候选表；不作解释 |
| 三方四正 | NOT_IMPLEMENTED | 无解释或评分 |
| 大限 | PARTIAL / DISPUTED | 局数起始与阴阳年性别顺逆候选 |
| 流年 | PARTIAL / UNCONFIRMED | 仅目标年份地支位置，不是完整流年推演 |

“limited_sanhe_foundation”只描述当前工程范围。由于命身宫、五行局、主星、四化和周期的传统来源尚未闭环，不得称为完整三合、飞星、四化或综合门派系统。

## 输入与失败边界

- 必填：农历年、月、日、闰月布尔值、时支索引、传统性别字段及人工核验来源。
- 月、日、时支只做 `1–12`、`1–30`、`0–11` 的结构校验；缺失或越界 fail closed。
- 未知或不确定时辰、闰月状态应在上游保存为候选资料，当前执行不猜值。
- “该年是否存在该闰月”及“该月是否有三十日”需要独立历法资料核验；当前核心没有自动历法，因此不能自行断言。输入资产明确记录此限制。

## Profile 与争议

`mechanical-trust-profiles-1.0.0.json` 不设默认 Profile：

- `ZIWEI.SANHE.MANUAL_LUNAR.LEAP_SAME_MONTH.V1`：闰月沿用本月；
- `ZIWEI.SANHE.MANUAL_LUNAR.LEAP_SPLIT_15.V1`：初一至十五沿用本月，十六日起按次月。

四化表、局数起限、顺逆和简化流年都保留独立字段和版本，但仍是 `UNCONFIRMED / research_active / production_activatable=false`。飞化、星曜解释、吉凶和宿世映射继续禁用。

## 来源与对照

五项原有传统 claim 的 `traditional_source` 仍为 `null`。本 Sprint 未虚构古籍、作者、页码或师承。

工程对照使用固定的 iztro `2.5.8`（commit `9d39f17`，MIT）作为独立开源实现。十二个 `mechanical_reference` 覆盖五局、命身宫差异、时支端点、月日边界与闰月 Profile 分歧；其中十一例对命宫、身宫、五行局和十四主星位置得到 `normalized_match`。这只能证明当前核心字段与该实现一致且可复现，不能证明门派纯度、四化、大限或传统解释正确。

新增案例聚合 Hash 记录在 `mechanical-trust-references-1.0.0.json`。旧 Output、Trace、Domain Hash 与所有既有聚合 Hash 不修改。

## Replay 与版本政策

- 旧 Ruleset、Profile、Output Hash、Trace Hash 和 Replay 保持不变；
- 新资产只增加可信基线，不改变 `calculate_chart` 输出；
- 若未来确认规则错误，必须新增方法、Profile 和 Ruleset 版本；
- 历史归档继续按旧版本 Replay，Reanalysis 才能显式选择新版本；
- 比较页必须显示输入、Profile、规则资产及候选字段差异。

## 尚待项目所有者与专家确认

1. 命身宫、五行局、十四主星的正式出版或可核验原典定位；
2. 闰月政策以及子时输入如何由上游历法转换；
3. 生年四化表的具体流派与版本；
4. 大限起始、顺逆、年龄口径和完整流年方法；
5. 合格审校人签署的人工排盘样例。

在上述事项闭环前，本基线保持研究态，不能晋升为生产默认。
