# Contributing

仓库尚未公开，也未选择最终开源许可证。项目所有者书面确认许可证和公开计划前，不接受外部贡献，也不改变仓库可见性。

内部变更必须：

1. 从最新 `main` 创建功能分支；
2. 不修改冻结的 Ruleset、Golden 或 Hash 来迎合新实现；
3. 不提交真实用户资料、完整外部数据、密钥、本机绝对路径或缓存；
4. 运行 Python、PostgreSQL、Web、视觉、Lighthouse、Secret、许可证和文档门禁；
5. 对用户可见变化补充键盘、移动端、错误状态和文本回退验证；
6. 保持 DeepSeek 与确定性核心隔离；
7. 通过普通 PR 审核，不强制推送、不绕过失败检查。

## Visual tests

视觉变更必须逐张审查 Linux 与 Windows 基线。不得通过提高像素差异阈值、批量接受 Snapshot、减少页面或设备矩阵、降低 Lighthouse 门槛，或使用 `skip`、软失败、`continue-on-error` 制造绿色结果。

仅更新真正受设计变更影响的平台和页面，并在提交说明中记录审核依据。CI 是 Linux 权威基线环境；Windows 使用独立基线，不能互相覆盖。

## Dependencies and licenses

新增依赖必须更新 `third-party-lock.json`、`THIRD_PARTY_NOTICES.md` 和 `sbom.cdx.json`，确认版本、许可证及分发边界。代码许可证、规则数据许可证、知识内容权利和测试数据许可分别治理；不得擅自加入最终开源许可证。
