# 紫微机械研究引擎 1.0

## 状态与边界

`ZIWEI.SANHE.MECHANICAL.RESEARCH.V1` 是 `traditional_mechanical /
research_active / UNCONFIRMED / production_activatable=false`。它不是
三际观原创算法，也不是正式命理解读。D-005 未冻结；自动公历转农历、
性格、吉凶、星曜组合解释、宿世、中阴、因缘、六象和 K 线均不输出。

每次执行必须显式提交 Profile ID 与版本。首版只接受人工核验的农历
年月日、闰月标记、时支索引和传统顺逆排所需的 `traditional_sex`；
历史法定时间与 IANA 时区作为上游 Calendar provenance 保存。系统不
静默把公历转换成农历，也不从姓名或其他字段推断性别。

## 传统原义、系统映射与工程假设

### 传统机械候选（尚待合格审校）

- `ZW-CLAIM-MINGSHEN-001`：寅起正月，顺数生月；命宫逆数生时，
  身宫顺数生时。
- `ZW-CLAIM-WUXINGJU-001`：以命宫干支纳音五行定水二、木三、
  金四、土五、火六局。
- `ZW-CLAIM-MAJOR-STARS-001`：以局数和农历日的商余定紫微，
  再安紫微与天府两系十四主星。
- `ZW-CLAIM-SIHUA-001`：生年干四化表为 Profile 资产，当前
  `UNCONFIRMED`，必须逐干审校。
- `ZW-CLAIM-DECADE-001`：局数为大限起始数，阳男阴女顺、阴男
  阳女逆；当前只形成宫位区间，不作运势解释。

这些 Claim 的书目候选来自公版《紫微斗数全书/全集》的安星法脉络，
以及项目方法选型证据包；尚未取得合格方法审校人的逐条签字，因此
不标成权威金样例。外部 `iztro` 只验证工程差分，不能证明传统正确性。

### 本系统二次结构化

字段名、索引从 0 开始、Canonical JSON、Trace step、资产 hash、
Replay Manifest、差分状态和 Profile 生命周期均为三际枢工程契约，
不是传统文献原义。

### 工程假设

- 宫位、星曜和运限列表使用固定顺序，避免平台排序差异。
- 离散计算只用整数；无二进制浮点评分。
- 闰月提供 `same_month_number` 与 `split_15` 两个显式研究候选。
- 辅星范围为空；没有来源审校就不输出占位结果。
- 流年基础只把目标年支定位到宫位，不产生任何吉凶。

## Trace 与 Replay

链路为：核验农历输入 → 闰月策略 → 时支 → 命身宫 → 十二宫与宫干支
→ 五行局 → 十四主星 → 生年四化候选 → 大限和流年基础。

Replay 校验输入、Profile、Ruleset、Profile/四化资产、Trace 与领域
hash。Profile 撤销后只允许在旧资产完整时回放，不得用新 Profile
替换历史结果。DeepSeek 和 Oracle 均不进入 Domain、Trace 或 Hash。
