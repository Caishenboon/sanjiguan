# GitHub Public 切换运行手册

本手册只在公开授权包完成后执行。它不构成当前公开授权。

## 切换前硬门禁

1. 合并开源封卷与签署记录，等待 `main` 六项 CI 全绿，0 failed、0 skipped、无软失败。
2. 运行 `python scripts/validate_open_source_release.py --require-public-ready`。
3. 确认 17 个受保护 Hash、Ruleset、Golden、Snapshot 与研究状态未改变。
4. 重新执行全历史 Secret Scan，并人工检查 Actions 日志和 Artifact。
5. 确认根许可证、版权/署名、`TRADEMARKS.md` 与第三方 NOTICE 已按签署决定生效。
6. 确认外部原始数据、私人资料、备份、运行时 `.env`、SSH 私钥和受限材料不在所有公开 refs。
7. 准备 `main` 保护规则与私密漏洞报告配置；GitHub Free 的相关公开仓库能力在切换后立即启用。

GitHub 官方说明指出，Private 切换为 Public 后，仓库内容、Actions 历史和日志会公开，任何人
可以 Fork；因此可见性切换必须是最后一步：

- <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility>
- <https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately>
- <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>

## 切换顺序

1. 核对仓库名称、默认分支、可见性和最终 `main` SHA，并准备好保护规则所需的唯一 Job 名称。
2. 由产品负责人亲自在 GitHub Danger Zone 确认切换为 Public。
3. 切换后立即启用 `main` 保护：禁止 force push/删除，要求 PR、必需状态检查和会话解决。
4. 切换后立即启用 Private Vulnerability Reporting。
5. 以未登录窗口验证 README、LICENSE、SECURITY、贡献指南和来源声明可访问。
6. 重新运行 `main` CI，确认六项 Job 全部实际执行并成功。
7. 核对 Secret Scan、Actions 日志可见内容、开放 Issue/Discussions 设置与安全报告入口。
8. 记录切换时间、执行人、公开 `main` SHA 与 CI Run。不要同时创建 Tag 或 Release。

## 失败回退

发现密钥、私人数据、受限内容或许可证错误时，先停止传播并记录最少证据，再按事件响应流程处理。
把仓库重新设为 Private 不能收回已经被克隆或 Fork 的内容，因此不能把“再改回 Private”视为可靠
撤销手段。

## 2026-08-25 执行记录

- PR #29 以普通 Merge Commit `f018dc02fbd50206e696f52b526344af43adfee3` 合并公开激活资产。
- 首次合并后 main Run `32764894491` 因真实 Merge Commit 使历史邮箱计数从 20 增至 21 而失败；失败记录保留，未降低门禁。
- PR #30 以普通 Merge Commit `90f3253a63cd877c4409bc97ca952d37695a7c85` 修正该证据计数；未引入新的邮箱值。
- 最终切换前 main CI [Run 32766173234](https://github.com/Caishenboon/sanjiguan/actions/runs/32766173234) 六项成功，0 failed、0 skipped、0 soft failure。
- 产品负责人在 GitHub 官方二次验证后完成 Private → Public 切换。
- `main` 已要求 PR、分支最新、讨论解决及六项必需 CI；管理员不得绕过，force push 与删除未开放。
- Private Vulnerability Reporting、Dependency Graph 与 Dependabot alerts 已启用。
- 未认证访问验证仓库主页、README、LICENSE 与 SECURITY 均返回 HTTP 200。
- Tag / GitHub Release 保持 `0 / 0`；生产规则未激活，外部数据 Connector 未启用，DeepSeek 未调用。
