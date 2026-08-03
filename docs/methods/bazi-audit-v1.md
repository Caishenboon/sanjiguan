# 八字机械实现审计 v1

## 当前实现

| 范围 | 实际行为 | 代码与测试 | 状态 |
|---|---|---|---|
| IANA 时区、DST、歧义/不存在时间 | `ZoneInfo` 解析历史 offset，显式标记 DST 边界 | `calendar/birth_time.py::normalize_birth_time`; `tests/test_calendar*` | 工程机械基座 |
| 地方平/视太阳时 | 保存法定时间，按经度和均时差产生候选；不改原输入 | `calendar/birth_time.py::build_time_candidates` | 计算可用，主盘方法未定 |
| 节气瞬时 | Astronomy Engine 搜索太阳黄经 15°整数倍 | `calendar/solar_terms.py`; `tests/test_sanji_engine_bazi_*` | 天文基座，不等于八字方法已冻结 |
| 年柱 | 立春瞬时换年 | `four_pillars.py::_year_pillar` | Profile 候选 |
| 月柱 | 十二节 start-inclusive 换月 | `four_pillars.py::_month_pillar` | Profile 候选 |
| 日柱 | proleptic Gregorian JDN + `day-epoch-1.0.0.json` | `four_pillars.py::_day_pillar` | 可重复但来源未闭环 |
| 时柱 | 23–01 起的十二时辰；时干从日干推导 | `four_pillars.py::_hour_pillar` | 与日界 Profile 联动 |
| 未知时辰 | 枚举覆盖区间并去重，最多 26 候选 | `four_pillars.py::calculate_four_pillars` | 已实现，不伪造时刻 |

源码路径均以 `packages/sanji-engine/src/sanji_engine/` 为根。完整字段记录见 `rule-audit-v1.json`。

## 三个现有 Profile

- `CIVIL_MIDNIGHT`：法定时间、00:00 换日。
- `APPARENT_ZICHU`：地方视太阳时、23:00 子初换日。
- `DUAL_SPLIT_ZI`：法定午夜与视太阳时早晚子时并列敏感性候选。

三者是研究候选，不是三个都正确，也没有隐藏默认。D-001 只冻结了“保存法定时间、同时计算地方视太阳时、换柱才双盘分析、不静默改时”；它没有冻结哪一盘为命理主盘。

## 四柱结构审计

已实现：年、月、日、时干支，干支索引以及基础阴阳五行参考表。

未实现或不应声称已完成：藏干、十神、月令解释、纳音解释、天干五合、六合、三合、三会、冲、刑、害、破、自刑、旺衰、格局、调候、喜忌、用神。即使以后加入藏干或五行统计，也不得把计数直接命名为旺衰结论。

## 运势结构

大运顺逆、起运岁数/时间、大运干支、流年和流月当前均不由八字引擎输出。`method-evidence-1.0.0.json` 收录的《事林广记》和《珞琭子三命消息赋注》只证明存在相应传统陈述，不能自动冻结现代 Profile。

## 争议与风险

1. 子初/子正/早晚子与先校正还是先换日：D-002 未冻结，P1。
2. 立春换年、十二节换月的天文时刻可计算，但传统采用与边界包含规则仍需审校，P1。
3. 日柱 epoch 仅有内部 checkpoint，缺独立权威金样例，P1。
4. IANA pre-1970 数据并非所有地区的法律权威记录；超出可靠区间需地区核验。
5. 当前支持 Gregorian 1900–2099；未实现各地历法改革历史。

## 当前行为样本

- 普通：三个 Profile 对非边界时刻通常给出同柱，并保留校正量。
- 边界：74 个 fixture 覆盖立春、十二节、日界、时辰、DST/时区与太阳时跨界。
- 缺失：未知出生时辰输出候选集合，不补中午或午夜。
- 争议：23:00/00:00 与视太阳时换界由 Profile 并列展示。

这些样本由 `tests/test_sanji_engine_bazi_conformance.py` 和 `tests/test_sanji_engine_bazi_four_pillars.py` 固定；是现状回放，不是传统权威金样例。
