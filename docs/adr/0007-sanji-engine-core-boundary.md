# ADR-0007：sanji-engine 独立确定性核心边界

状态：Accepted（2026-07-23）

## 决策

采用 `packages/sanji-engine` 与 Python import `sanji_engine`，最低 Python 3.11。
Engine API 1.0 仅公开 `validate_request`、`execute`、`replay`、
`inspect_ruleset`。核心不得依赖 Next.js、FastAPI、PostgreSQL、网络或
DeepSeek；应用只可经公开契约调用。

Canonical JSON 固定为 `jcs-rfc8785-subset/1.0.0`：当前稳定域仅接受
null、布尔、Unicode 字符串、安全整数、列表和字符串键对象；拒绝二进制
浮点和非标量代理码位，键按 UTF-16 排序，SHA-256 标为 `sha256:<hex>`。
数字表达、空值、列表顺序及哈希排除字段均属版本契约，不得静默变更。

确定性评分优先使用整数基点；确需小数时必须声明 Decimal 精度及
ROUND_HALF_EVEN。排名必须定义完整固定 tie-breaker。本 Sprint 不迁移或
激活任何未确认评分。

规则状态机为：
`draft + disabled + UNCONFIRMED` → `review_candidate + disabled` →
`research_active` → `production_active`；撤销使用
`revoked_for_future_runs`，不得覆写历史 bundle。

## 边界与后果

- Calendar 是首个等价迁移模块；发现旧缺陷只登记差异。
- Signals/Inference 只冻结为 `research_baseline`，不代表权威、正确或生产批准。
- 未确认模块返回结构化 `MODULE_DISABLED`，结果必须为 null。
- 输入、规则 bundle、逐步 Trace、Replay Manifest 和输出分别有版本与哈希。
- `run_id` 与运行/回放传输意图不参与计算输入哈希；列表顺序保持语义。
- 许可证、规则数据权利、知识内容权利与测试数据许可继续分别未定；仓库保持 Private。

## 拆仓

当前不创建第二仓库。只有经批准方案中的十二项拆仓条件全部满足，并由产品
负责人书面确认后，才允许拆仓或发布。
