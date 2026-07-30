# 命势长图、人生 K 线与三际断章 v1

## 定位

这是三际观原创的确定性研究模型，不是传统既定 K 线算法，不是证券价格预测，也不
声明现实预测准确率。

```text
授权记录与机械结构引用
  → 规范化因素
  → 同事件去重 / 同源折扣 / 递减收益
  → 时间桶 → 整数 OHLC
  → Strength / Confidence / Coverage
  → 吉凶状态与应期窗口
  → 确定性断章 → 可选受控成文
  → 加密持久化 / 三际录 / Replay / Reanalysis / Compare
```

## 时间桶与 OHLC

支持日、月、季、年和多年阶段。自动模式选择不高于最粗输入精度的粒度。只有年份的
事实覆盖整年，不会补成具体事件日。时间轴分为 `observed_past`、`current_state`、
`projected_future` 和 `insufficient_gap`。

未来投影至少需要两个独立的既往有效证据组，并按距离降低 magnitude 与 confidence。
空白窗口没有 Candle，不随机插值。

Open 等于上一有效桶 Close；High/Low 是窗口内按日期、稳定 ID 和内容 Hash 排序后的
确定性因素路径极值；Close 是窗口末累计势位。所有数值为整数 basis points，范围
`-10000..10000`。页面除以 100 显示为 `-100..100`。

Coverage 只反映资料通道覆盖，不贡献 OHLC。重复来源不会增加独立证据数或势位，
同一组的后续证据按 Ruleset 递减收益。

## 吉凶、应期与受控成文

吉凶包括吉、平、凶、吉中有阻、凶中有解、吉凶相争和资料不足。它综合势位、支持、
逆证、冲突、Confidence 与边界敏感，不等同于 Close 正负。

应期始终是窗口，携带精度、触发条件、增强/削弱因素、Strength、Confidence、支持、
逆证与 Trace。输入不支持具体日期时只输出月、季、年或阶段。

无 `DEEPSEEK_API_KEY` 时仍生成完整确定性报告。可选 DeepSeek 调用只允许七个文辞
字段，不能修改姓名、年代、地点、身份、死因、轮回次数、债务、OHLC、吉凶、应期、
排序、证据或 `【可能】`。梦境、关系、日记全文、完整地址、数据库 ID 和 Trace 原文
不进入 Provider 输入。

无密钥、未获本次确认、超时、无效 JSON、额外字段、伪经典、确定语气升级、未授权
日期、吉凶覆盖或认识状态删除，都会触发确定性回退。

## 隐私、Replay 与版本比较

输入、核心结果、确定性文辞和 AI 文辞分别加密。Hash 基于 Canonical 明文，随机
Nonce 不影响核心 Hash。私人表全部 `FORCE ROW LEVEL SECURITY`。

原版本 Replay 使用不可变输入快照；Reanalysis 读取当前有效证据并新建记录。比较
列出输入增删、Engine、Ruleset、Policy、粒度和精度变化，不覆盖历史结果。彻底删除
输入快照后返回 `replay_unavailable`，不得伪造恢复。
