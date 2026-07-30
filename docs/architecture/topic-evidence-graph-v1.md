# 专题证据图与确定性专题引擎 v1

状态：`sanji_original / research_active / UNCONFIRMED / production_activatable=false`。

本架构服务宿世观、中阴观与缘契观。它是三际观原创研究模型，不是古籍已有算法，也不证明历史身份、轮回事实、灵界事实或命定关系。

## 共享边界

三类专题共用一条内核：

`授权记录引用 → 规范化事实 → Canonical Topic Evidence Graph → 去重 → 候选 → Strength / Confidence / 状态 → Trace / Replay`

图使用普通 Python 数据结构与 PostgreSQL JSONB 加密快照，不使用图数据库。节点和边均有稳定 ID、规则版本和内容哈希；输入先排序，同一输入和版本在 Windows/Linux 上必须得到相同哈希。图只保留用户确认的结构标签和记录引用，不复制梦境、关系或日记正文。

节点包括主体、关系、人生事件、行为模式、愿向、梦境标签、机械盘引用、时间窗、过渡片段、专题候选、身份候选、债务候选、证据组、缺失与冲突。边包括支持、逆证、冲突、派生、重复、延续、中断、先后、涉及、对应、确认、撤销、亏欠、偿还与未竟。

## 认识状态

`observed` 是用户直接记录；`mechanically_derived` 是确定性机械结构；`rule_inferred` 是规则推演；`generated_identity` 是确定性生成姓名；`historical_candidate` 是有来源的历史人物候选；`contested` 与 `insufficient` 分别表示相争和资料不足。

界面统一使用产品词典添加 `【可能】`、`【历史人物候选·可能】`、`【相争】` 或 `【可能·资料不足】`。用户事实不添加“可能”。

## Strength、Confidence 与状态

Strength 只累计有效、去重后的指向力度；Confidence 衡量独立记录数、来源可靠度、日期精度与冲突。Coverage 和机械结构不会直接增加 Strength。同源记录只保留最强一项；贡献使用整数 basis points 和递减收益。

状态为 `decisive / provisional / contested / insufficient`。宿世观即使资料不足仍生成三组低可信研究候选，但不会把候选陈述为事实。

## 专题边界

- 宿世观：确定性生成姓名、年代范围、地区候选、身份、死因候选、轮回序位与因果债务。姓名不是历史人物匹配；当前历史人物候选接口为空。
- 中阴观：人生过渡与离世过渡两个模式。离世模式必须存在明确离世记录；禁止预测在世主体的死亡时间、死法或寿命。
- 缘契观：严格区分单方观察和双方允许合参；不输出命定伴侣、唯一真爱或必然复合。

DeepSeek、Oracle、随机数、向量相似度和网络服务均不参与事实、命名、评分、排序、状态、Trace 或 Hash。

## 持久化与删除

`topic_executions` 保存加密输入、图和结果快照；新分析创建新行。三际录用 `topic_execution_id` 引用专题执行。Replay 使用原快照，Reanalysis 使用当前有效记录。彻底删除快照后应返回 `replay_unavailable`，不得伪造恢复。所有私人表启用并强制 RLS。
