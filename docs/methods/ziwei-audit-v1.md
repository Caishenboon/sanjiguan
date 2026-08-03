# 紫微斗数机械实现审计 v1

## 当前实现矩阵

| 项目 | 当前行为 | 代码位置 | 审计状态 |
|---|---|---|---|
| 公历转农历 | 不实现；要求 `manual_verified_lunar_input` | `ziwei/mechanical.py::calculate_ziwei_mechanical` | 明确缺口 |
| 闰月 | `LEAP_SAME_MONTH` 与 `LEAP_SPLIT_15` 两个 Profile | `::_effective_lunar_month` | DISPUTED |
| 命宫、身宫 | 月数与时支候选公式 | `::_life_body_palaces` | UNCONFIRMED |
| 十二宫与宫干 | 固定顺序及五虎遁候选 | `::calculate_ziwei_mechanical` | UNCONFIRMED |
| 五行局 | 命宫干支/纳音候选 lookup | `::_five_element_bureau` | UNCONFIRMED |
| 十四主星 | 内嵌 offset 表 | `::_major_star_positions` | UNCONFIRMED |
| 生年四化 | 候选表 `birth-year-transformations-candidate-1.0.0.json` | `::_birth_year_transformations` | DISPUTED |
| 大限/流年 | 局数起限、阴阳年性别顺逆、简化流年支 | `::_decade_cycles` | PARTIAL / DISPUTED |

源码根为 `packages/sanji-engine/src/sanji_engine/`。五个核心 claim 在 `ziwei/assets/source-claims-1.0.0.json` 中的 `traditional_source` 全部为 `null`，所以“测试通过”只能表示机械稳定，不能表示流派正确。

## 未实现

- 自动公历/农历转换及历法权威来源；
- 经过审校的辅星、煞星范围；
- 宫干飞化与完整飞星解释；
- 完整三方四正推理；
- 命主、身主；
- 庙旺落陷；
- 完整大限、流年、流月与解释；
- 任何星曜吉凶、身份或宿世解释。

因此当前实现不能称为某一门派的完整论命系统。“受限三合基础排盘结构”是产品范围描述，不是传统权威认证。

## 混派审计

代码把命身宫、五行局、十四主星、生年四化和周期结构放入同一机械结果，但尚无来源证明这些表完全属于同一传承版本。它是便于差异研究的共享结构，不应被称为已完成三合、飞星、河洛或四化门派。

## 当前行为样本

- 普通：人工核验的非闰月输入生成十二宫、五行局和十四主星。
- 边界：测试覆盖所有月份/时支、五局、十四星与闰月 Profile 差异。
- 缺失：没有人工核验农历输入时 fail closed，不猜测农历日期。
- 争议：闰月 16 日后，两 Profile 明确输出不同结果。

`tests/test_sanji_engine_ziwei.py` 固定输出、Trace、Domain Hash 与 Replay。当前没有由合格审校人签署的传统权威金样例。

## V1 冻结前置条件

1. 为命身宫、五行局、十四主星、四化与大限分别补正式来源和页码/版本。
2. 至少两组合法可用的人工排盘样例，记录流派、闰月和子时政策。
3. 项目所有者选择闰月和四化 Profile；未选择时继续研究态。
4. 飞化解释保持禁用；不得用合成 fixture 代替传统审校。
