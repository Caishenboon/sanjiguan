# ADR 0014：确定性命势时序与受控三际断章

状态：Accepted（research-only）
日期：2026-07-30

## 决定

命势长图、人生 K 线、吉凶、应期和三际断章结构全部收敛到
`packages/sanji-engine` 的 `life-chart` 边界。首版规则资产为
`life-trend-rules/1.0.0`，统一标记：

- `tradition_scope = sanji_original`
- `activation = research_active`
- `review_status = UNCONFIRMED`
- `production_activatable = false`

K 线内部只使用整数基点 `-10000..10000`。Coverage 与 Confidence 不直接改变
势位；没有事实的时间桶保留空白，不插值。八字、紫微、易经和专题推演输出只可
作为结构引用，未经审校的解释性 Mapping 不得产生势位、吉凶或应期。

DeepSeek 不进入核心边界。系统先生成完整确定性报告；外部模型只接收最小、已锁定
摘要并润色七个文本字段。Schema、事实白名单或认识状态校验失败时，丢弃模型文本并
使用确定性回退。

## Hash 边界

- `core_output_hash`：时间桶、OHLC、吉凶、应期及断章结构。
- `deterministic_report_hash`：版本化模板成文。
- `narrative_input_hash`：外部模型最小输入。
- `narrative_output_hash`：保存的模型文辞或回退文辞。

核心 Replay 只承诺重现确定性 Hash；历史 AI 文辞保存原响应，不承诺再次调用外部
模型逐字一致。

## 后果

同输入、数据版本、引擎版本和 Ruleset 在 Windows/Linux 产生相同核心 Hash。规则
尚未经过现实有效性验证，页面和 API 必须持续显示研究态声明。
