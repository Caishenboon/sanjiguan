# 当前状态

```yaml
product: 三际观
engine: 三际枢
release: 1.0.0-rc.1
default_branch: main
release_candidate_pr: 27
engineering_rc_ready: true
ai_handoff_ready: true
new_machine_handoff_ready: true
merge_ready: true
open_source_engineering_closure_ready: true
open_source_ready: false
public_release_authorized: false
repository_visibility: private
production_rules_active: false
llm_in_deterministic_core: false
database_migration_count: 24
```

## 已完成

邀请制 Owner/Member 会话、主体与完整出生原始记录、六类记录、三际录、易经实物三钱、
八字和紫微研究结构、六象、宿世、中阴、缘契、命势长图、确定性三际断章、导出、删除、
Replay、Reanalysis、比较、Docker 冷启动和虚构恢复演练已经接到真实 API 与 PostgreSQL。

## 仍未完成

生产传统/原创规则激活、正式许可证、公开仓库、Tag/Release、生产 KMS、数据地区、备份
保留和删除 SLA、外部数据再分发授权、restricted/sealed 内容治理和现实有效性验证。

所有传统 Profile 及三际原创规则保持
`research_active / UNCONFIRMED / production_activatable=false`。DeepSeek 是可选成文层；无
密钥时完整结构和确定性报告仍可用，CI 不调用付费服务。

当前 migration 为 `0001`–`0024`。受保护 Hash 的完整机器清单见
[`project-manifest.json`](project-manifest.json)；最近传统组合与 Replay Hash 分别为
`sha256:675ac443dc5868c38255593cad2f711880aa1a315a010a5bfb6189a9fd2253c2` 与
`sha256:1ba7afc7323ec93c708f4a733460b80d2fe8f7e438520dfff79ad7cd480dd8e9`。

当前 CI 门禁包括双平台引擎确定性、双平台视觉、PostgreSQL 16 migration/RLS/E2E、
Python/API、Web、Storybook、Lighthouse、Gitleaks、Schema/OpenAPI、许可证、V1 冷启动和
恢复演练。

PR #27 已以普通 Merge Commit 合并为主干基线 `c7101f0d0955e583e111509ce83784b587b39196`；
[main CI Run 32705480100](https://github.com/Caishenboon/sanjiguan/actions/runs/32705480100)
六项全部成功。V1.2 产品质量与诸象仪器没有修改三际枢、Ruleset、Profile、Golden、migration
或受保护 Hash。视觉与状态截图采用完全虚构数据，详见
[`docs/product/evidence/manifest.json`](../product/evidence/manifest.json)。

下一步是独立开源发布封卷。机器工程边界已经可以验证，但正式许可证/署名主体、20 个非
`noreply` 历史提交邮箱、合格知识边界审查、公共人物法律审查和负责人最终 Public 授权仍是
硬阻断。详见 [`public-release-closure-v1.md`](../open-source/public-release-closure-v1.md)。
在这些决定完成前不能公开仓库、创建 Tag/Release、激活生产规则或启动新术数体系。
