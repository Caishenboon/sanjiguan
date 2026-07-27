# Bazi Method Profile 与 Conformance Contract

## 边界

`sanji-engine` 内的 `bazi` 目录只承载方法档案、来源包、边界输入和一致性验证。
它不计算四柱，也不向应用层公开新的根入口。

```text
Profile registry ─┐
Evidence bundle ──┼─> Conformance Harness ─> method-policy diff + stable hash
Boundary cases ───┘                         └> pillar_results = null

Engine API validate_request ─> require explicit profile
Engine API execute          ─> MODULE_DISABLED
```

根 API 仍只有：

- `validate_request`
- `execute`
- `replay`
- `inspect_ruleset`

## Profile 规则

- Schema：`bazi-method-profile/1.0.0`
- 状态只能为 `draft` 或 `review_candidate`
- `production_activatable=false`
- `selection_authority=CANDIDATE_ONLY_NOT_OWNER_DECISION`
- 每项政策必须列出选项、显式候选值、决定状态和决策引用。
- `content_hash` 排除自身字段后使用 Engine JCS 子集计算。
- 未选择 Profile 时拒绝请求；没有隐式默认值。

## Conformance 失败分类

| code | 含义 |
|---|---|
| `DATA_MISSING` | Profile、字段、Claim、Locator 或案例缺失 |
| `PROFILE_NOT_FOUND` | Profile ID 未登记 |
| `PROFILE_MISMATCH` | 字段、状态、选项或 Profile 组合不符合契约 |
| `PRODUCTION_GATE` | 试图启用生产或冒充 Owner 最终选择 |
| `ASSET_DRIFT` | Profile、证据或案例的内容哈希漂移 |

## 输出契约

Conformance 输出只包括：

- Profile ID 与 Profile hash；
- 每项方法政策的结构化差异；
- 案例分类与预期政策差异；
- 证据包、案例包和整体内容 hash；
- `calculation_performed=false`；
- `pillar_results=null`。

不得添加天干、地支、四柱、十神、旺衰、吉凶或模型生成的占位结果。

## 回放与版本

任何 Profile、Claim、Locator、案例或 Canonical 规则变化必须提升对应资产版本。
历史 conformance 结果按 Profile hash、证据 hash 和案例 hash 回放。未来正式引擎不得
把新 Profile 静默应用于旧运行。
