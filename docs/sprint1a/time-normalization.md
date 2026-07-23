# 时间规范化与天文组件

## 数据链

`原始记录 → 历史法定时间 → 地方平太阳时 → 地方视太阳时 → 边界检测 → 候选盘输入集合`

原始输入始终保留。系统不覆盖用户时间，不设置命理主盘；候选项的
`is_primary_chart` 固定为 `false`。输出限于校正分钟数、时辰/日界/节气边界
是否变化，以及因此敏感的后续规则。

## 方法与版本

- 历史法定时间：Python `zoneinfo` + IANA tzdata 2025.2。输入保存 IANA zone ID、
  数据库名和记录时声明的版本。歧义或不存在的本地时间拒绝静默猜测。
- 地方平太阳时：以当时法定 UTC offset 扣除 DST 后得到标准子午线，
  每经度差按 4 分钟校正。
- 地方视太阳时：地方平太阳时叠加 NOAA 分数年公式的均时差。该公式是工程近似，
  不属于传统术数规则。
- 节气瞬时：Astronomy Engine 2.1.19 搜索太阳视黄经。组件只给出天文瞬时，
  不决定月柱、起运或八字结论。

## 验证边界

IANA 样例覆盖上海、纽约夏令时、伦敦夏令时、加德满都非整点偏移、
基里巴斯日期变更线与纽约 DST 缺失时段。节气样例取香港天文台 2025 年历的
春分、夏至、秋分、冬至，允许误差 120 秒。

120 秒仅是这四个样例的验收阈值，不是全时代精度声明；进入生产前需扩展年份、
时区和节气全集，并冻结 ephemeris/ΔT/黄经定义。

## 来源

- IANA Time Zone Database: https://www.iana.org/time-zones
- NOAA Solar Calculation Details: https://gml.noaa.gov/grad/solcalc/solareqns.PDF
- Astronomy Engine: https://github.com/cosinekitty/astronomy
- 香港天文台 2025 年历: https://www.hko.gov.hk/en/gts/astron2025/files/HKO_almanac_2025.pdf
