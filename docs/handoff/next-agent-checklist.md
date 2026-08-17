# 下一位 Agent 开工清单

- [ ] 完整阅读根 `AGENTS.md` 与本目录 README、当前状态、决策边界。
- [ ] 检查当前 Git 分支、HEAD、工作树和 remote，不覆盖他人改动。
- [ ] 获取最新 `main`，检查所有 Open PR 及目标分支。
- [ ] 运行 `python scripts/check_secrets.py` 和 `python scripts/check_portability.py`。
- [ ] 运行 `python scripts/validate_handoff.py`，核验规则仍是研究态。
- [ ] 运行对应历史 Hash/Golden 门禁，不改期望值掩盖差异。
- [ ] 在 PostgreSQL 16 空库执行 migration 两次并检查漂移。
- [ ] 阅读任务对应 ADR、方法 Profile、来源登记与嵌套说明。
- [ ] 只在新的、明确命名的功能分支施工。
- [ ] 完成后运行任务要求的单元、集成、跨平台、Web、视觉和安全测试。
- [ ] 保持仓库 Private，除非产品负责人在当前任务中明确授权公开。
- [ ] PR 保留失败记录；不得 skip、软失败、降低阈值或批量接受 Golden/Snapshot。
