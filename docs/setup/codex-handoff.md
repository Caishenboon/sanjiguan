# 新电脑上的 Codex 接手

新任务从仓库根目录开始，不依赖旧聊天或旧电脑路径。推荐第一条指令：

```text
请先完整阅读根目录AGENTS.md、docs/handoff/README.md、
docs/handoff/current-state.md和docs/setup/codex-handoff.md。
在修改任何文件前，核验当前分支、工作树、未合并PR、Ruleset状态、
Migration和历史Hash。不得让LLM参与确定性算法，不得自行激活生产规则，
不得改变仓库可见性。完成核验后只汇报当前状态，不立即施工。
```

Codex 应执行 `docs/handoff/next-agent-checklist.md`，使用相对路径和跨平台命令，并把
产品负责人决策边界视为硬门禁。任何本机密钥、私有数据和备份都不应进入上下文、日志、
补丁或提交。
