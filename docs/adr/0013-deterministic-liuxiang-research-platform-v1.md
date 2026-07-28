# ADR-0013：确定性六象研究平台 v1

- 状态：Accepted for research implementation
- 日期：2026-07-28
- 范围：research only

## 仓库盘点

主干已有单一 `sanji-engine` 边界、Signal/Inference 研究基线、Trace、Replay
与 RFC 8785 兼容规范化 JSON。旧 30 例聚合哈希为
`a08cb815b1ba65f16c4873b4c6cfac6653220a7d5630078a654beb36935ea96c`。
机械资产包括易经三钱 4096 状态、八字 74 边界与 420 项机械验证、多
Profile、紫微基础结构，以及仅用于差分测试的 Oracle。数据库已有执行
Manifest、RLS；API、设计系统、Storybook、Playwright、双平台视觉门禁
与第三方许可证登记均已存在。本 ADR 不另建框架、仓库或数据仓库服务。

## 六象定义盘点与决策

当前研究 UI 稳定使用：

| 稳定 ID | 名称 | 机器名 | 定义来源 |
|---|---|---|---|
| `lx_ming` | 命象 | `natal_structure` | 当前六象总览与出生资料缺失提示 |
| `lx_ye` | 业象 | `habitual_pattern` | 立卷采集“长期习惯、困扰与反例” |
| `lx_yuan` | 愿象 | `vow_and_action` | 立卷采集“愿心、承诺与行动” |
| `lx_meng` | 梦象 | `dream_record` | 立卷采集“反复梦境” |
| `lx_yuan_relation` | 缘象 | `relationship_evidence` | 经同意关系或匿名事件 |
| `lx_shi` | 世象 | `life_event` | 人生事件与时间线 |

这些名称只说明仓库产品契约，不声称传统原义。资产统一标记：

```text
tradition_scope = sanji_original
activation = research_active
review_status = UNCONFIRMED
production_activatable = false
```

早期采集界面另有“感应象”，而当前总览以“命象”占六项之一。此处是
真实定义冲突，已登记为 `lx_ganying_candidate`，保持 `disabled`，不把
二者暗中合并。完整定义资产位于
`packages/sanji-engine/src/sanji_engine/rulesets/assets/liuxiang-dimensions-1.0.0.json`。

## 决策

1. Signal v1 原样可读、可 Replay；Signal v2 使用新 Schema 和记录，不就地升级。
2. 六象 v1 复用现有 Signals/Inference 模块入口，通过规则集分派，不创建第二套框架。
3. 所有最终算术使用整数 basis points；乘法采用 round-half-even。
4. Strength 只表示有效支持减逆证；Confidence 单独表示来源、映射、独立性、
   完整度、Profile、边界、冲突与质量。
5. 相同事实+映射完全去重；同 `shared_source_group` 在同维度、同方向只保留
   最强贡献。重复同源不会增加独立计数、Strength、Confidence 或排名。
6. 易经、八字、紫微适配器只输出机械事实。没有已审方向规则时不生成 Signal，
   返回资料不足，不以临时解释填充。
7. Oracle、DeepSeek、外部数据均不进入确定性 Hash 或锁定字段。
8. 外部研究数据单独建表、单独资产分级，不进入用户 Profile 或证据表。
9. DreamBank 原始授权链未闭环；只登记书目信息，连接器禁用，正文不下载。

## 后果

平台能够用合成数据证明确定性、去重、状态机、Trace、Replay 与跨平台 Hash；
不能证明六象现实预测力。外部观察只能生成规则候选报告，候选默认
`draft/disabled`，不得自动回写 Ruleset。
