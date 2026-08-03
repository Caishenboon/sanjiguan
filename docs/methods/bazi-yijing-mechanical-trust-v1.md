# 八字与易经三钱机械可信基线 v1

状态：`research_active / UNCONFIRMED / production_activatable=false`。本资产冻结当前工程行为和争议边界，不把候选方法宣布为唯一正统，也不启用传统解释。

## 1. 八字日柱 JDN / epoch 审计

当前入口为 `sanji_engine.bazi.four_pillars.calculate_four_pillars`。`_jdn_gregorian` 使用 Fliegel–Van Flandern 风格的整数 Gregorian JDN，`_day_index` 使用：

```text
(anchor_cycle_index + JDN(date) - JDN(anchor_date)) mod 60
```

基准资产仍是 `bazi-day-epoch/1.0.0`：`1949-10-01 = cycle_index 0 = 甲子`。美国海军天文台公开的 Gregorian/JD 转换公式可核验 JDN 工程部分；它不能证明这个干支日锚点属于传统共识。锚点缺正式版本、页码、合格方法审校人与签字边界案例，因此继续标记 `UNCONFIRMED / RESEARCH_ONLY`，没有替换 epoch，没有创建新 Ruleset，也没有改变历史输出。

独立实现对照分三层：

- `sxtwl 2.0.7` 来自独立项目与代码库，Linux CI 对普通案例执行实时差分；它是独立工程对照，不是传统权威。
- `lunar-python 1.4.8` 与 `tyme4py 1.5.0` 均固定版本和上游提交，但来自同一提供方，只算两套外部实现，不伪称两份独立传统证据。
- 23:00 附近两套外部实现出现日柱/时柱政策差异，正好证明子时规则必须按 Profile 并列，不能多数投票。

来源与版本化结论见 `bazi/assets/day-epoch-evidence-1.0.0.json`。

## 2. 八字时间 Profile

`bazi/assets/mechanical-trust-profiles-1.0.0.json` 冻结以下工程政策：

| 范围 | 当前行为 | 传统状态 |
|---|---|---|
| 年界 | 立春天文瞬时，起点包含 | UNCONFIRMED |
| 月界 | 十二节天文瞬时，起点包含 | UNCONFIRMED |
| 法定时间 | 原样保存，不静默改写 | 产品决定已冻结 |
| 历史时区 | IANA named zone、历史 offset 与 DST | 工程事实 |
| 太阳时 | 同算地方平太阳时与地方视太阳时 | 工程事实；命理主盘未冻结 |
| 未知时辰 | 枚举 13 个分段、去重，不补造时刻 | 工程政策 |
| 日界 A | 法定时间午夜换日 | 流派候选 |
| 日界 B | 地方视太阳时子初 23:00 换日 | 流派候选 |
| 日界 C | 午夜盘与早晚子时分轨并列 | 流派候选 |

三个 Profile 无默认项。真太阳时不隐藏启用；只有显式选择对应 Profile 才参与计算。视太阳时造成换年、换月、换日或换时柱时，候选和边界标志同时保留。

## 3. 新机械 Golden

`mechanical-trust-goldens-1.0.0.json` 包含 13 例：普通日期、立春前后、十二节前后、23:00、00:00、DST 有效时刻与不存在时刻、历史时区、不同经度、未知时辰和 Profile 分歧。

每例记录输入、IANA 时区、经度、Profile、期望四柱或结构化拒绝、来源、人工复核状态和独立对照状态。期望值由固定外部实现、官方天文/时区资料与人工差异审查建立，不把当前引擎输出反向包装成传统权威 Golden。该组分类为 `mechanical_reference`，传统专家复核仍待完成。

新聚合 Hash：

```text
sha256:20cba2932d0d800590aa26fd0dd954f5c621d194c909f0a638844dced836b139
```

## 4. 易经三钱 2 / 3 契约

稳定 Canonical 输入是整数 `2` 与 `3`，不是自然语言“正面/反面”或 `heads/tails`：

| 三钱和 | 状态 | 本爻 | 是否动 | 变爻 |
|---|---|---|---|---|
| 6 | 老阴 | 阴 | 是 | 阳 |
| 7 | 少阳 | 阳 | 否 | 阳 |
| 8 | 少阴 | 阴 | 否 | 阴 |
| 9 | 老阳 | 阳 | 是 | 阴 |

每次三枚钱求和，六次投掷严格自初爻到上爻。当前界面 Profile 把“正面”映射为 3、“反面”映射为 2；这只是版本化的钱面标签。历史资料对有字/无字、面/背的阴阳归属存在差异，因此持久化的 2/3 才是 Replay 权威。

历史直接录入 6/7/8/9、`yijing-three-coin-mechanical-0.1.0`、4096 状态输出和旧 Hash 均不变。新增资产 `yijing/assets/coin-value-profile-1.0.0.json` 不进入既有 Engine Result Hash。

三钱机械层只形成六爻、本卦、动爻和变卦，不是完整六爻纳甲。纳甲、世应、六亲、六神、月建、日辰、旬空、旺衰、用神与完整断卦均为 `NOT_IMPLEMENTED`。

## 5. 展示与兼容

现有最小展示已经满足：八字研究页显式选择 Method Profile 并显示候选/边界/Replay；易经结果研究详情显示 Profile、Ruleset 和版本；合参入口明确“四柱机械排盘不是完整八字论命”，易经结果明确“不生成吉凶、应期或完整六爻解释”。本 Sprint 未改页面结构或视觉基线。

旧 Ruleset、Golden、Snapshot、数据库与业务结果均未修改。Reanalysis 只有在未来项目所有者批准新方法版本后才可显式选择新版；旧归档继续按原版本 Replay。

## 6. 可核查来源

- US Naval Observatory, “Converting Between Julian Dates and Gregorian Calendar Dates”: https://aa.usno.navy.mil/faq/JD_formula.html
- IANA Time Zone Database Theory: https://data.iana.org/time-zones/tzdb/theory.html
- Hong Kong Observatory, “The 24 Solar Terms”: https://www.hko.gov.hk/en/gts/time/24solarterms.htm
- Hong Kong Observatory, “Heavenly Stems and Earthly Branches”: https://www.hko.gov.hk/en/gts/time/stemsandbranches.htm
- `sxtwl 2.0.7`: https://github.com/yuangu/sxtwl_cpp
- `lunar-python 1.4.8`: https://github.com/6tail/lunar-python
- `tyme4py 1.5.0`: https://github.com/6tail/tyme4py
- 《困学纪闻》卷一所载三钱 6/7/8/9 陈述（文本线索，版本与传统审校仍需完成）：https://ctext.org/wiki.pl?chapter=909326&if=gb&remap=gb
- 《祛疑说》所载钱面阴阳歧义（用于证明标签争议，不作为唯一规则来源）：https://ctext.org/wiki.pl?chapter=471318&if=gb&remap=gb

不得从这些工程对照推出传统解释正确性，也不得把公开文本线索直接晋升为生产断法。
