# sanji-engine 1.0 契约与迁移地基

```text
Web / API / LLM
       |
       v（仅四个公开入口）
sanji_engine.public
       |
       +-- schemas / rulesets / canonical / trace / replay
       +-- calendar（research_active，等价迁移）
       +-- signals / inference（disabled，research_baseline）
       +-- bazi / ziwei / yijing / past-life / bardo /
           relationship / life-chart（draft + disabled + UNCONFIRMED）
```

## 公开契约

- `validate_request(request)`：版本、字段、确定性上下文、规则 bundle 和
  可哈希类型校验。
- `execute(request)`：生成版本化模块结果、逐步 Trace、Replay Manifest 与哈希。
- `replay(manifest, request)`：校验 manifest、bundle、输入和 Trace 等价性。
- `inspect_ruleset(bundle_id)`：返回含内容哈希的不可变 bundle 快照。

应用层不得导入 `sanji_engine.calendar` 等内部路径，也不得复制计算公式、
评分常量或规则分支。DeepSeek 既不是依赖，也不进入哈希或锁定字段。

## 版本策略

Engine API、请求/结果 Schema、Canonicalization、规则 bundle、数据版本和
模块 method_id 独立版本化。破坏性契约变更升级 API/Schema；任何会改变哈希
的规范变更升级 canonicalization 版本；规则改动创建新 bundle，历史版本保留。

## 数据迁移

`0011_sanji_engine_manifest_foundation.sql` 仅增加可空 manifest 字段与格式约束。
旧行保持 NULL，明确表示 legacy/unavailable；禁止推断或伪造历史 replay
manifest。本 Sprint 不迁移生产历史数据。

## 审校门禁

规则晋级必须满足来源、流派、责任人、合法金样例、跨平台确定性、逆证与回放
审计。`research_baseline` 只防漂移，不能替代权威金样例。未满足时始终返回
`MODULE_DISABLED`。
