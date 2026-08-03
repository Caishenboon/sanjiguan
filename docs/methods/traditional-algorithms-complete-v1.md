# 传统术数算法完整 V1

状态：`research_active / UNCONFIRMED / production_activatable=false`。本交付固定三套可重放的研究 Profile，不声称覆盖所有八字、紫微或六爻流派，也不把三际观的证据聚合描述为传统古法。

## 固定边界

```text
固定上游 → 只读 Adapter → Canonical 结构 → 版本化 Profile/Ruleset
        → Trace/Replay → Canonical Evidence Graph → 三际观原创合参
```

DeepSeek、Oracle 和网络服务均不参与排盘、权重、强弱、格局、用神、吉凶、应期、排名或 Hash。三个体系先独立计算；只有用户正式起卦且提供明确问题类型时，六爻才进入合参。

## 八字：bazi-ziping-complete-v1

Ruleset：`bazi-ziping-complete-1.0.0`。机械排盘、藏干、十神和运程来自固定 `lunar-python 1.4.8`；传统结构复用既有不变的四柱与传统结构 Ruleset。完整 V1 新增：

- 月令、明暗十神、根气、透干以及生扶/克泄耗事实；
- 以公开证据单位计算的极弱、偏弱、中和、偏强、极强；
- 月令主气形成的十类格局候选、从强/从弱候选及相争状态；
- 寒暖候选与扶抑候选并列，冲突不强行合并；
- 用神、喜神、忌神仅作为 `provisional/contested` 候选；
- 大运顺逆、起运偏移、十年大运和流年结构，以及可追溯的结构方向。

当前强弱 Profile 使用月令支持、可见支持、根气和泄耗的离散证据单位与整数比率，不使用隐藏浮点权重。其来源比较包括 `Sudo-Biao/suangua@9cf2783…`；该实现的现代解释性长文未被摄入，传统正确性仍待人工审校。农历输入、IANA/DST、太阳时和未知时辰继续由既有 Calendar/四柱候选链处理；换柱必须并列候选，不在本 Adapter 内静默改时。

## 紫微：ziwei-sanhe-complete-v1

Ruleset：`ziwei-sanhe-complete-1.0.0`。固定 `iztro 2.5.8@9d39f17…` 提供公历/农历转换、闰月合法性、十二宫、命身宫、五行局、命主身主、十四主星、核心辅煞、四化、大限和流年/流月/流日/流时结构。

每宫按本宫、两三合宫与对宫形成证据组。吉辅类别、煞曜类别和四化分别作为独立结构组；不会把单星分值简单相加。十二宫均输出强度、可信度、支持、逆证和相争状态。闰月 Profile 必须显式提供；当前固定 Profile 对应 `iztro_fix_leap_true`，旧 `LEAP_SAME_MONTH/LEAP_SPLIT_15` 研究资产继续保留，未被覆盖。本 V1 是三合基础 Profile，不是飞星、河洛或所有紫微门派大全。

## 六爻：liuyao-jingfang-najia-v1

Ruleset：`liuyao-jingfang-najia-1.0.0`。实物三钱仍以单枚 `2/3` 和六次自下而上为 Canonical 契约；历史直接录入 `6/7/8/9` 不变。固定 Apache-2.0 快照 `yaomancy/liuyao-engine 0.1.0@562b902…` 提供八宫、纳甲、世应、六亲、六神、伏神、本卦与变卦；`bopo/najia 2.0.1` 只作差分，不是第二份独立真值。

完整 V1 记录月建、日辰、旬空输入，并逐爻计算空、月破、日冲、动变、回头生克与进退候选。明确问题类型映射用神；一般趋势无唯一用神时返回 `insufficient`，不会隐藏选一个。所有动爻参与计算。吉、平、凶、吉中有阻、凶中有解和相争来自公开整数证据单位；应期只输出范围与触发条件，不制造必然精确日期。

## 合参、Hash 与兼容

`sanji-traditional-composite-1.0.0` 将三个 Canonical 结果转为 Evidence Graph。每个固定上游/机械事实 Hash 只形成一个独立组；同源重复不能增加强度或可信度。Strength 与 Confidence 分开，冲突和缺失保留。新分析才使用新 Ruleset；历史档案仍按旧版本 Replay，Reanalysis 创建新记录。

新基线：

- 上游锁定：`sha256:63d6bf9166e2b9b718b3270e6dc6d9b939ba349346b331d17b304d619b521592`
- 八字 60 例：`sha256:a595504b9f4806c74f7fb7935bf720ee2256d437c1253dfaf4e61cca60494a73`
- 紫微 48 例：`sha256:40594f6e1fe71938b3d357b6f2ab31059596eee46252a80d7407bd78e7e5fd6d`
- 六爻 4096 状态：`sha256:76a0dd1092cec8b6e41adf3a6037226fd8b24d16bf03a74b3a365ac8541b92e2`
- 合参 12 例：`sha256:675ac443dc5868c38255593cad2f711880aa1a315a010a5bfb6189a9fd2253c2`

这些是工程一致性资产，不是现实准确率、权威金样例或专家签署。

## 持久化、API 与页面

迁移 `0021_traditional_algorithms_complete_v1.sql` 建立加密、Owner-only、`FORCE ROW LEVEL SECURITY` 的执行表。API 前缀为 `/api/v1/admin/research/traditional-complete`，提供 execute、get、Replay、Reanalysis 和 compare；OpenAPI 在 [traditional-algorithms-complete.openapi.json](../api/traditional-algorithms-complete.openapi.json)。研究页为 `/admin/research/traditional-complete`，普通用户不会在主导航看到它。

## 来源与许可证

机器清单见 `third_party/traditional-v1-upstream-lock.json`，许可证副本见 `LICENSES/`，人类可读说明见 `THIRD_PARTY_NOTICES.md`，依赖清单见 `sbom.cdx.json`。拒绝无可核验许可证的 `china-testing/bazi` 和无法独立取得来源/许可的 `richard3153/bazi-calculator`。上游现代文辞、AI Prompt 和经典长文本不进入仓库。

## 尚存研究限制

- 八字强弱、格局、调候和用神的传统审校尚未完成，不能作为跨流派共识；
- 紫微三合证据组是本 V1 的固定研究 Profile，不代表飞星或河洛体系；
- 六爻断法只覆盖当前固定问题类型和结构规则，不是所有古今断法大全；
- 新结果不会反向修改六象、宿世、中阴、缘契、命势或旧三际断章；
- 在产品负责人和合格专家确认前，三个 Ruleset 均不能生产激活。
