# Sprint 20A Final Audit

状态：最终自检补充；仅修正审计陈述，不改变任何业务输出。代码事实基线为 PR #20 的 `f3372bdc78468c69aa2f86181a1595870fa24fa7`。

## 八字代码事实矩阵

共同 Ruleset：`bazi-four-pillars-research-1.0.0`；方法 `BAZI.FOUR_PILLARS.MECHANICAL.RESEARCH.V1/1.0.0`；`research_active / UNCONFIRMED / production_activatable=false`。

| 项目 | 状态 | 实际入口/函数 | 测试证明 |
|---|---|---|---|
| 四柱入口 | IMPLEMENTED | `bazi/four_pillars.py::calculate_four_pillars` | 三 Profile、Replay、跨平台 Hash |
| 年柱 | IMPLEMENTED | `::_track_result`，1984 甲子索引 | 60 年循环、边界 fixture |
| 立春换年 | IMPLEMENTED | `::_lichun` + `::_track_result`，`at_or_after` | 立春跨界和太阳时换柱 |
| 月柱 | IMPLEMENTED | `::_surrounding_jie_wall` + `::_track_result`，十二节 start-inclusive | 十二节精确边界全覆盖 |
| 节气计算 | IMPLEMENTED | `calendar/solar_terms.py::solar_term_instant`，Astronomy Engine 2.1.19 | 节气瞬时和 74 边界资产 |
| 日柱 | IMPLEMENTED / UNCERTAIN authority | `::_jdn_gregorian`, `::_day_index` + `bazi-day-epoch/1.0.0` | 周期与内部独立 checkpoint；缺权威传统 golden |
| 子时换日 | PARTIAL / DISPUTED | `::_track_result` 读取 Profile 的 `midnight`、`zichu_23`、split-Zi 策略 | 23:00、00:00、早晚子差异；D-002 未冻结 |
| 时柱 | IMPLEMENTED | `::_track_result`，23–01 后每两小时；日干组推时干 | 十二时辰与特殊子时覆盖 |
| 五行统计 | NOT_IMPLEMENTED | 无生产函数；`_pillar` 只返回干支和索引 | 无正向测试；静态范围门禁 |
| 藏干 | NOT_IMPLEMENTED | 无生产函数 | 静态范围门禁 |
| 十神 | NOT_IMPLEMENTED | 模块声明禁止；无 `calculate_ten_gods` | `test_bazi_package_contains_no_pillar_algorithm` 与解释为空 |
| 旺衰/格局/用神 | NOT_IMPLEMENTED | 无生产函数 | `interpretation=None`、规则静态门禁 |
| 大运/流年 | NOT_IMPLEMENTED | 无生产函数 | 无正向输出；D-003 未冻结 |

结论：这是多 Profile 四柱机械研究基座。存在“机械排盘可重复，但传统解释体系完全缺失”的明确状态；不能称完整八字论命。

## 紫微代码事实矩阵

共同 Ruleset：`ziwei-sanhe-research-1.0.0`；方法 `ZIWEI.SANHE.MECHANICAL.RESEARCH.V1/1.0.0`；五个核心 claim 的 `traditional_source` 均为 `null`。

| 项目 | 状态 | 实际入口/函数 | 测试证明 |
|---|---|---|---|
| 农历转换 | NOT_IMPLEMENTED | `ziwei/mechanical.py::calculate_chart` 只接受 `manual_verified_lunar_input` | 非人工核验输入 fail closed |
| 闰月 | PARTIAL / DISPUTED | `::_effective_month`，same-month 与 split-15 两 Profile | 两 Profile 差异测试 |
| 命宫/身宫 | IMPLEMENTED / UNCONFIRMED | `::calculate_chart` 的 `life_index/body_index` | 12 月 × 12 时支覆盖 |
| 五行局 | IMPLEMENTED / UNCONFIRMED | `::_cycle_index` + `NAYIN_ELEMENTS/BUREAU` | 五局可达 |
| 紫微星定位 | IMPLEMENTED / UNCONFIRMED | 日数/局数 quotient-remainder 与 `ziwei_index` | 十四星完整性测试 |
| 十四主星 | IMPLEMENTED / UNCONFIRMED | 内嵌 offset 表与 `::calculate_chart` | 14 星唯一性/可达性 |
| 辅星 | NOT_IMPLEMENTED | `approved_auxiliary_stars=[]` | 明确禁用状态 |
| 生年四化 | PARTIAL / DISPUTED | 候选表 `birth-year-transformations-candidate/1.0.0` | 仅结构和版本测试；来源未审校 |
| 三方四正 | NOT_IMPLEMENTED | 无生产函数或输出字段 | 无正向测试 |
| 大限 | PARTIAL / DISPUTED | `decade_cycles`：局数起限、候选顺逆 | 12 段结构测试；方法来源未确认 |
| 流年 | PARTIAL / DISPUTED | `annual_position` 仅目标年地支位置 | 结构存在；不是完整流年推演 |

体系判断：名称和产品范围倾向“受限三合基础机械候选”，但代码同时携带未审校的生年四化与周期候选；既不是完整三合体系，也不是飞星体系、完整四化体系或可认定的综合门派。最准确名称是“仅机械排盘的有限研究候选”。混派风险为 P1。

## 易经代码事实矩阵

Ruleset：`yijing-three-coin-mechanical-0.1.0`；方法 `YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1/1.0.0`。

| 项目 | 状态 | 实际入口 | 测试证明 |
|---|---|---|---|
| 三钱起卦 | IMPLEMENTED | `yijing/three_coin.py::cast_physical_three_coin` | 2/3 输入校验及 4096 状态 |
| 本卦、动爻、变卦 | IMPLEMENTED | `LINE_STATES`、上下卦与 King Wen asset lookup | 0/1/6 动爻、64 卦、Replay、跨平台 |
| 纳甲、六亲、世应、六神 | NOT_IMPLEMENTED | 无生产函数/资产 | 静态范围和解释禁用 |
| 月建、日辰、旬空、旺衰、用神 | NOT_IMPLEMENTED | 无生产函数/资产 | 静态范围和解释禁用 |

结论：只有三钱起卦机械层，不是完整六爻纳甲断卦。多动爻当前只展示并机械变卦，不存在解释策略。

## 来源最终审查

- `CONSENSUS_MECHANICAL`：IANA 时间处理、天文节气定义、干支/卦序等明确机械结构；技术来源只证明其技术范围。
- `SCHOOL_SPECIFIC`：真太阳时用于命盘、立春/十二节应用策略、三钱 2/3 约定。
- `DISPUTED`：子时换日、闰月、四化、大限顺逆与起始。
- `UNCONFIRMED`：八字日柱 epoch 的传统权威闭环、紫微五项核心表/公式。
- `SANJI_ORIGINAL`：六象和下游融合，不得回填为传统来源。

未发现虚构古籍、作者、师承、门派或出版信息。无法确认者继续标 `UNCONFIRMED`。

## 红队

| 风险 | 等级 | 原因 |
|---|---|---|
| 排盘可重复被误写成完整八字论命 | P1 | 十神、藏干、旺衰、格局、用神和运势均未实现 |
| 紫微混派/权威错觉 | P1 | 核心来源为空，四化和周期候选与“Sanhe”命名共存 |
| 三钱机械被误称完整六爻 | P1 | 纳甲至用神整层缺失 |
| Profile 只隔离部分争议 | P1 | 八字年/月界和日柱 epoch、紫微四化/周期尚未全部成为独立可选 Profile |
| 用户认为“不准” | P1 | 边界 Profile 不同、未知时辰、人工农历输入、解释层缺失而 UI 若未充分说明 |
| 工程正确但传统争议巨大 | P1 | 子时、真太阳时、闰月、四化、大限 |
| 辅助传统模块缺失 | P2 | 功能范围有限但未造成现有机械错误 |

本轮未发现 P0：没有跨平台漂移、Replay 破坏、数据损坏、安全或隐私问题。

## 蓝队

应保留：显式 Profile 且无隐藏默认、Ruleset/资产独立版本、Canonical Hash、Trace/Replay、旧版本回放、候选差异展示、未确认规则 fail closed、解释层与三际原创层隔离、跨平台 fixtures。架构能够支持多流派实验和用户选择，但前提是将每个争议规则完整下沉到 Profile，而不是只靠文档说明。

## Sprint 20B 建议（不执行）

| 优先级 | 项目 | 价值 | 复杂度 | 历史影响 | 专家确认 |
|---|---|---|---|---|---|
| A | 八字日柱 epoch 独立来源与签署 goldens | 防止全局日/时柱偏移 | 中 | 可能；必须新版本 | 必须 |
| A | 冻结或明确长期并列 D-002、真太阳时、年/月界 Profile | 解决主要边界不一致 | 高 | 可能 | 必须 |
| A | 紫微命身宫、五局、十四星、四化、周期来源闭环 | 消除混派与权威风险 | 高 | 可能 | 必须 |
| A | 易经钱面约定正式来源与用户契约 | 防止整卦反转误解 | 低 | 可能 | 必须 |
| B | 藏干、十神、关系结构独立传统 Profile | 提升机械结构完整度 | 中 | 新增输出 | 必须 |
| B | 紫微自动历法转换和权威闰月样例 | 降低人工输入错误 | 高 | 可能 | 必须 |
| B | UI 完成度与方法状态门禁 | 防止用户误解“完整/准确” | 中 | 不应改变核心结果 | 产品+专家 |
| C | 旺衰、格局、调候、用神、大运 | 长期传统解释能力 | 很高 | 新规则版本 | 必须 |
| C | 完整飞化/三方四正及高级周期 | 扩展紫微门派 | 很高 | 新规则版本 | 必须 |
| C | 独立六爻纳甲体系 | 完整易经断法研究 | 很高 | 新方法族 | 必须 |

## 验收不变性

Final Audit 只新增/修正文档和审计登记。PR 保持 Open；仓库保持 Private；不创建 Tag/Release；不修改算法、Ruleset、Golden、Snapshot、数据库或历史 Hash。
