# 八字基础排盘方法现状盘点

状态：Sprint 仅冻结工程表达，不冻结流派，不实现四柱算法。

## 仓库事实

| 范围 | 状态 | 依据 |
|---|---|---|
| 原始出生记录、IANA 时区、经纬度、时间精度 | 已实现工程结构 | `docs/sprint1a/time-normalization.md`、`packages/sanji-engine/src/sanji_engine/calendar/` |
| 保存历史法定时间，同时计算地方视太阳时；换界才双轨敏感性 | D-001 已冻结 | `docs/decisions/product-owner-confirmation.md` |
| Calendar 的民用时间、地方平太阳时、地方视太阳时与节气瞬时 | 已实现研究基础 | `packages/sanji-engine/src/sanji_engine/calendar/` |
| Calendar 选择哪一个时间作为命理主盘 | 没有规则，明确禁止 | `docs/adr/0007-sanji-engine-core-boundary.md` |
| 子初/子正换日、早晚子时、跨日次序 | D-002 未冻结 | `docs/decision-register.md` |
| 节气如何切年柱/月柱、边界等于瞬时如何包含 | 只有天文组件，没有命理规则 | `docs/decisions/method-selection-dossier.md` |
| 旺衰、喜忌、起运、顺逆大运 | D-003 未冻结；不属于本 Sprint | `docs/decisions/product-owner-confirmation.md` |
| 八字 Engine 模块 | `BAZI.UNCONFIRMED`、disabled | `packages/sanji-engine/src/sanji_engine/rulesets/` |
| 执行结果 | 结构化 `MODULE_DISABLED`、`result=null` | `packages/sanji-engine/src/sanji_engine/disabled.py` |
| 权威八字金样例 | 不存在 | 现有 `tests/golden/sprint0-inputs.json` 仅是占位/边界输入 |

## 已决定内容

1. 原始法定时间不得被静默修改。
2. IANA named zone、历史 UTC offset、DST、地点和经纬度必须可追溯。
3. 同时生成地方平太阳时与地方视太阳时天文候选。
4. 只有候选时间跨越后续边界时，才进入双轨敏感性；工程层不选择主盘。
5. 未知时间保留候选区间，不伪造时刻。
6. 未显式选择 Method Profile 不得运行八字方法验证。
7. 所有当前 Profile 均不可生产激活。

## 尚未决定内容

- 年柱是否以立春天文瞬时切换。
- 月柱是否只按十二“节”切换，以及“节/中气”取法。
- 恰好等于边界瞬时的包含侧。
- 日柱采用民用午夜、子初或早晚子时分拆。
- 时柱使用民用、平太阳或视太阳时间。
- 真太阳时跨日后，日界规则与校正的先后次序。
- 格里历改革前按历史当地历法，还是使用外推格里历。
- 生产支持的历史日期范围和地点精度下限。
- D-003 的旺衰、起运和顺逆方法。

## 冲突与证据限制

- D-001 冻结“双轨敏感性”，但不等于“地方视太阳时是唯一传统正统”。
- HKO/天文历算只能证明节气物理瞬时，不能证明八字年/月柱必须怎样切换。
- IANA tzdb 提供 named-zone 历史，但其早期记录会修订；不能把数据库猜测包装成确定历史事实。
- 已定位的公版传统文本可证明某些起运/顺逆主张存在，不能据此冻结 D-003，更不能推导 D-002。
- `tests/golden/sprint0-inputs.json` 的 `UNCONFIRMED` 项不是权威金样例。

## 只有接口但没有规则

- `calendar.normalize_birth_time` 生成三个时间候选和边界敏感标志。
- `calendar.solar_term_instant` 生成太阳黄经瞬时。
- Engine API 能验证明确 Profile，并始终对八字返回 `MODULE_DISABLED`。

这些接口没有年柱、月柱、日柱、时柱计算语义。

## 只有研究草案

- `BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1`
- `BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1`
- `BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1`

三者仅用于区分政策影响。它们不是流派定论，不是产品默认，也不是正式八字算法。

## 不得激活

年/月/日/时柱、十神、藏干解释、五行强弱、格局、调候、用神、神煞、起运、大运、
流年、吉凶、宿世映射和六象映射均不在本 Sprint，并继续受静态门禁阻断。
