# Contributing

仓库尚未公开，也未选择最终开源许可证。外部贡献流程在许可证决定前保持关闭。

内部变更必须：

1. 从最新 `main` 创建功能分支；
2. 不修改冻结 Ruleset、Golden 或 Hash 来迎合新实现；
3. 不提交真实用户资料、外部完整数据、密钥、本机绝对路径或缓存；
4. 运行 Python、PostgreSQL、Web、视觉、Lighthouse、Secret、许可证和文档门禁；
5. 对用户可见变化补充键盘、移动端、错误状态和文本回退；
6. 保持 DeepSeek 与确定性核心隔离；
7. 通过普通 PR 审核，不强制推送或绕过失败检查。

视觉变更必须逐张审查 Linux/Windows 基线。不得直接提高 Diff 容差、批量接受
Snapshot、降低 Lighthouse 门槛或用 `skip`/软失败制造绿色。

新增依赖需更新 `third-party-lock.json`、`THIRD_PARTY_NOTICES.md` 和
`sbom.cdx.json`，并确认许可证与分发边界。
