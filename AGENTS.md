# 三际观工程交接约束

三际观是面向少数授权使用者的研究系统；三际枢是其确定性核心。当前阶段为
`1.0.0-rc.1` 工程候选，项目所有者已授权开源，所有传统与三际原创推演规则仍是研究态。

V1.1 产品质量工作只允许改进语言、旅程、展示、错误边界、PWA 公共壳、安全和可维护性；
不得借产品优化改写三际枢、Ruleset、Profile、Golden、Replay 或受保护 Hash。

> 术数引擎定象，规则引擎成断，DeepSeek只成文。

## 开工前

依次阅读 `docs/handoff/README.md`、`docs/handoff/current-state.md`、
`docs/handoff/decision-boundaries.md`、`docs/project-structure.md` 和任务对应 ADR/方法文档。
随后核验分支、工作树、未合并 PR、规则状态、migration 漂移、Secret Scan 与历史 Hash。

## 真实目录

- `packages/sanji-engine/`：唯一确定性算法核心；公开入口仅在 `sanji_engine.public`。
- `apps/web/`：Next.js Web/PWA；不得复制算法或持有供应商密钥。
- `apps/api/`：FastAPI、鉴权、应用服务、持久化和受控成文网关。
- `infra/migrations/`：顺序、不可改写的 PostgreSQL migration 与 RLS。
- `packages/sanji-engine/src/sanji_engine/schemas/`、`schemas/`：版本化契约。
- `packages/sanji-engine/src/sanji_engine/rulesets/`、`packages/rules/`：规则资产。
- `prompts/`：受控成文模板；不能覆盖结构结果。
- `knowledge/`：来源、授权与知识治理；restricted/sealed 内容不得摄入。
- `tests/`、`packages/sanji-engine/src/sanji_engine/golden_cases/`：门禁与固定案例。

## 常用命令

```bash
python scripts/init_env.py
docker compose up --build
python -m unittest discover -s tests -p "test_*.py"
python scripts/validate_v1_release.py
python scripts/validate_handoff.py
python scripts/check_portability.py
python scripts/check_secrets.py
cd apps/web && pnpm install --frozen-lockfile && pnpm build && pnpm test:visual
```

环境建立、备份、恢复与跨机步骤见 `docs/setup/` 和 `docs/operations/`。

## 不可破坏的边界

- LLM 不得计算、选择或修改排盘、Signal、证据、权重、排名、吉凶、应期或 Hash。
- 不得混合未经标注的传统流派，不得伪造经典、师承、作者或来源。
- 不得就地修改旧 Ruleset 改变历史结果；新行为必须新版本并保留 Replay。
- 不得批量更新 Golden 或 Snapshot 掩盖漂移；受保护 Hash 见
  `docs/handoff/project-manifest.json`。
- 不得把 `research_active / UNCONFIRMED / production_activatable=false` 写成生产共识。
- migration 只能追加；不得改写已合并 migration。私人表必须 FORCE RLS。
- API、Web 与成文层只能调用核心契约，不得复制评分常量或规则分支。
- 不得提交密钥、私人数据、备份、受限文献、本机绝对路径或本地数据库目录。

## Ruleset、Replay 与 PR

新增 Ruleset/Profile 时登记来源、流派、版本、内容 Hash、review/activation 状态、
兼容影响和 Golden；未审校规则默认 disabled。原版本 Replay 使用原输入快照、Engine、
Ruleset、Policy、Profile 与数据版本；当前版本 Reanalysis 必须新建记录并明确差异。

只在独立分支施工。提交前运行任务要求的完整门禁、staged/worktree Secret Scan、链接和
跨平台确定性检查；PR 保留失败记录，不用 skip、软失败或降低阈值制造绿色。

以下事项仍须等待产品负责人书面确认：生产规则激活、Tag/Release、规则/知识范围扩大、
restricted/sealed 内容、外部数据 Connector 重新启用、生产 KMS、数据地区、备份保留和
删除 SLA。代码与当前原创内容许可证及仓库 Public 已于 2026-08-24 获得授权。Codex、
LLM 或无资质审核者不得代替传统/传承审校人。
