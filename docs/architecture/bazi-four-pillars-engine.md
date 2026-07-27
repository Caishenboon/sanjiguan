# 八字多 Profile 基础四柱引擎契约

## 边界

公开调用仍只有 `validate_request`、`execute`、`replay`、`inspect_ruleset`。应用端使用
`bazi-four-pillars-research-1.0.0`，并显式提交 Profile ID 和版本。核心不依赖 Web、
FastAPI、PostgreSQL、网络或 DeepSeek。

```text
原始出生记录
  → IANA 历史法定时间 / UTC
  → Profile 时间轨道（民用或地方视太阳时）
  → 立春与十二节瞬时
  → 版本化日序与换日政策
  → 年/月/日/时柱
  → 候选、Trace、Domain hash、Replay Manifest
```

## 三个 Profile 1.0.0

| Profile | 时间轨道 | 日界 | 时干所用日 | 候选行为 |
|---|---|---|---|---|
| `BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1` | 民用时间 | 00:00 | 有效民用日 | 已知时间 1 个 |
| `BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1` | 地方视太阳时 | 23:00 子初 | 子初换日后的有效日 | 已知时间 1 个 |
| `BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1` | 民用午夜 + 视太阳时早晚子时并列 | 民用轨 00:00；早晚子时轨日柱 00:00 | 晚子时的时干引用下一日，早子时引用当日 | 已知时间最多 2 个 |

共同政策：公历研究窗口 1900–2099；年界为立春天文瞬时；月界为十二“节”的天文
瞬时；边界采用起点包含、终点不包含；不设主盘。

每条时间轨道还逐柱声明 `pillar_time_basis.year/month/day/hour`。1.0.0 三个
Profile 的四柱均使用各自轨道时间；视太阳时轨因此会显式报告校正是否跨越年界、
月界、日界或时辰界。该逐柱映射属于工程化 Profile 政策，不被伪称为统一传统原义。

## 机械公式

- 六十干支按 10 干和 12 支同序循环，索引范围 0–59。
- 年柱研究索引：`(立春边界后的公历年 - 1984) mod 60`。
- 月支由立春起寅月，按十二节推进；月干按年干组与寅月偏移机械推导。
- 日柱将前公历日期先转为整数 JDN，再相对
  `bazi-day-epoch/1.0.0` 的 `1949-10-01 = 甲子` 研究锚点取模。
- 时支为 `23:00–01:00` 子时，此后每两小时一支；时干按日干组和子时偏移推导。

上述“传统机械表关系”可由香港天文台的[天干地支表](https://www.hko.gov.hk/en/gts/time/stemsandbranches.htm)
核查；十二节气黄经由香港天文台的[二十四节气表](https://www.hko.gov.hk/sc/gts/time/24solarterms.htm)
核查；公历到 Julian Date 的工程路径参考美国海军天文台的
[转换公式](https://aa.usno.navy.mil/faq/JD_formula)。日序锚点仍明确标记为
`source_attested=false`，不能因工程交叉验证而晋升为权威金样例。

## 输入与输出

输入必须包含出生日期、可空出生时间、时间精度、公历类型、IANA 时区、地点名称、
经纬度、坐标精度、用户确认状态、字段来源、Profile ID 和版本。非法、歧义 DST、
不存在的本地时间、越出研究窗口或版本缺失均返回结构化错误。

结果包含 Profile、Calendar/节气/日序/边界资产版本、候选四柱、边界标志、缺失数据、
完整 Trace 和 Replay Manifest。`interpretation`、`auspiciousness` 和
`manifestation_period` 固定为 `null`。

## 未知时间

未知时间按早子、丑至亥、晚子共 13 个起点包含/终点不包含区间枚举。单轨 Profile
最多 13 个候选，双轨最多 26 个；候选以 ID 和轨道稳定排序，不截断、不猜测时辰，
不依据人生事件回填。相同区间且四柱干支完全相同的候选按稳定键去重，原始方法轨道
及各自修正链保存在 `equivalent_tracks`，不会因去重丢失方法差异证据。
`unknown`、`hour`、`double_hour` 和 `half_day` 精度均按“无法安全确定单一时柱”
保守枚举；只有 `second` 和 `minute` 可进入单一已知时刻路径。

## Replay 资产

Replay 同时校验输入哈希、Ruleset、Profile 注册表及 Profile 内容、Calendar、节气
数据、日序锚点、74 例边界资产版本、Domain hash 和 Trace hash。撤销版本仅可在资产
仍存在时执行历史回放，不得由新 Profile 替代。
