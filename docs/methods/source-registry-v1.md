# 传统方法来源登记 v1

## 可信等级

- A1：官方技术标准/机构资料，只支持其明确技术范围。
- A2：可核验公共领域原典或可靠影印/整理，仅证明文本陈述存在。
- B1：正式出版专业资料，需记录版本、页码及流派。
- C：项目内部代码、决策或资产，可证明当前行为，不能证明传统权威。
- U：来源缺失或未完成审查。

## 已登记来源

| ID | 名称/机构 | 对应规则 | 等级 | 流派与版权边界 |
|---|---|---|---|---|
| SRC-IANA-TZDB | IANA Time Zone Database Theory, https://data.iana.org/time-zones/theory.html | 历史时区、DST | A1 | 工程时区资料；早期历史有限；遵循 tzdb notice |
| SRC-USNO-EOT | US Naval Observatory, Equation of Time, https://aa.usno.navy.mil/faq/eqtime | 平太阳时与视太阳时差 | A1 | 只支持天文定义，不决定八字用时 |
| SRC-HKO-SOLAR-TERMS | 香港天文台二十四节气, https://www.hko.gov.hk/en/gts/time/24solarterms.htm | 太阳黄经和节气瞬时 | A1 | 只支持天文瞬时，不决定立柱方法 |
| SRC-ASTRONOMY-ENGINE | Astronomy Engine 2.1.19, https://github.com/cosinekitty/astronomy | 节气瞬时计算依赖 | A1/开源实现 | 记录固定版本与许可证；不是传统来源 |
| SRC-SHLG-JUAN11 | 《事林广记》续集卷十一（维基文库传本） | 起运三日折一年、顺逆陈述候选 | A2 候选 | 需版本/文字校勘及流派审校；不大段复制 |
| SRC-LUOLUZI | 《珞琭子三命消息赋注》（维基文库传本） | 顺逆陈述候选 | A2 候选 | 同上；不能单独形成生产规则 |
| SRC-UNICODE-YIJING | Unicode Yijing Hexagram Symbols Names List, https://www.unicode.org/charts/nameslist/n_4DC0.html | 六十四卦字符名称/序号对照 | A1 结构 | 不支持三钱或断卦方法 |
| SRC-BZ-DAY-EPOCH | `bazi/assets/day-epoch-1.0.0.json` | 日柱 epoch | C | 内部资产；缺独立来源与权威 goldens |
| SRC-BZ-REFERENCE-TABLES | `bazi/assets/mechanical-reference-tables-1.0.0.json` | 干支参考表 | C | 需补正式来源登记 |
| SRC-ZW-CLAIMS | `ziwei/assets/source-claims-1.0.0.json` | 紫微五项核心候选 | U | `traditional_source=null`；禁止称传统确认 |
| SRC-YJ-CODE | `yijing/three_coin.py` | 三钱 2/3、6/7/8/9、爻序 | C | 当前契约，不是传统权威来源 |
| SRC-D002 | `docs/decisions/decision-register.md` D-002 | 子时换日 | U | 未冻结 |
| SRC-SANJI-BOUNDARY | 三际观规则与 ADR | 原创融合层 | C | `sanji_original`，代码与规则数据权利分开 |
| SRC-NONE | 无来源 | 未实现项 | U | 不得编造补齐 |

## 来源政策结论

官方天文和时区资料能证明时间计算方法，却不能批准八字或紫微流派。内部 fixture 能证明当前输出稳定，却不能成为传统权威金标准。下一阶段需要正式出版物的版本/页码、公共领域原典校勘和合格方法审校人共同闭环；有版权限制的资料只记录书目信息与短小事实，不全文摄入。
