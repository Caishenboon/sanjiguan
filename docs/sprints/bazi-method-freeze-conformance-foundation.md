# 八字方法冻结与验证基座 Sprint 交付说明

## 交付范围

- 三个版本化、不可生产激活的候选 Method Profile。
- 12 项 Claim、10 个 Locator，区分 Owner 决定、工程事实、传统主张和证据缺口。
- 74 个完全合成的机器可读边界案例，其中包含一个改革前历法待审案例。
- Conformance Harness：验证 Profile、来源引用、案例、Canonical 输出、稳定哈希和结构化差异。
- Engine 请求必须显式给出 Profile；八字结果仍为 `MODULE_DISABLED`。
- Owner-only 研究页面；无普通用户排盘入口。

## 案例分类

| 分类 | 用途 |
|---|---|
| `mechanically_verified` | IANA/Calendar 可重复验证的时间输入行为 |
| `profile_discriminating` | 只显示不同候选政策会在哪些边界分歧 |
| `source_attested` | 预留给有精确来源和来源方法说明的案例 |
| `pending_manual_review` | 未经合格审校，不进入正式验收哈希 |

本轮没有伪造 `source_attested` 八字命盘，也没有“权威四柱金样例”。

## 跨平台基线

- Profile 顺序固定的 Conformance hash：
  `sha256:6eb4eba309e9054e9fc1b698a90bf7e55522c7e663f1e497f09fe2ea1964dc02`
- Boundary asset hash：
  `sha256:d7d521b8205a27d659957bafd4b993e4fe8fb29909e1b9f145a792de8e3a6db1`

Calendar 基线 output hash 因请求新增显式 Profile ID 与 Profile 数据版本而更新。Calendar
结果和 Trace 行为没有变化；这是确定性请求信封变更，不是天文算法变更。

## 来源

- IANA tzdb theory：named-zone 历史、DST 与早期资料限制。
- USNO Equation of Time：平太阳时、视太阳时、经度差和均时差。
- 香港天文台二十四节气：15° 黄经间隔、十二中气与十二节气。
- 维基文库公版《事林廣記·續集·卷十一》与《珞琭子三命消息賦注》：仅登记其具体起运/
  顺逆主张；不用于冻结 D-002，也不直接激活 D-003。

## 明确未实现

年柱、月柱、日柱、时柱、十神、五行强弱、格局、调候、用神、神煞、起运、大运、
流年、吉凶、宿世、正式六象映射。
