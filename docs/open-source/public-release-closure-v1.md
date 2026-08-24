# 开源发布封卷 V1

> 2026-08-24 更新：项目所有者已激活分层许可证、接受当前 Git 历史、确认公开署名与
> 商标政策，并授权 Public。PR #28 已合并，main CI Run 32721037735 六项成功。
> 当前最小公开范围进一步把 VedAstro Connector 默认关闭；仍不分发外部原始数据、真实
> 人物 Fixture、restricted/sealed 内容或具体修法。下文保留最初封卷基线及风险演变记录。

本封卷审计基线为 PR #27 的普通 Merge Commit
`c7101f0d0955e583e111509ce83784b587b39196`，以及合并后
[main CI Run 32705480100](https://github.com/Caishenboon/sanjiguan/actions/runs/32705480100)。
六个必需 Job 全部成功，0 failed、0 skipped、0 soft failure。仓库在审计期间保持
Private，Tag / Release 为 `0 / 0`。

封卷只审查“能否安全公开代码仓库”，不确认术数现实有效性，不激活任何生产规则，也不
替代律师、版权人或传统/传承审校人的判断。

## 已完成的工程封卷

- 当前树与 staged/worktree Secret Scan、绝对路径扫描通过；main CI 使用 Gitleaks 扫描全历史。
- 17 个受保护 Hash 保持；未修改 Ruleset、Profile、Golden、评分、阈值、migration 或业务结果。
- `research-data/` 未跟踪 CSV、Parquet 或完整外部数据；VedAstro Manifest 明确禁止原始再分发。
- DreamBank 仅登记书目与字段，正文 Connector 禁用，正文未提交、未嵌入、未发送外部 LLM。
- `knowledge/` 跟踪内容只有三际观原创研究结构；未发现 restricted/sealed 全文、现代译文或修法步骤。
- 26 张产品证据由合成路由生成；Manifest 声明无真实用户、无 Provider 输出、无 DeepSeek 调用。
- GitHub Actions 顶层权限为 `contents: read`；未授予 write、packages 或 OIDC 权限。
- README、SECURITY、CONTRIBUTING、NOTICE、SBOM、第三方锁定与知识边界文档齐备。

机器结论记录于 [`public-release-manifest.json`](public-release-manifest.json)。

## 不能由工程扫描代替的决定

### 1. 正式许可证和署名主体

根 `LICENSE` 当前明确“不授予公开许可”。候选方案是：

- 项目原创软件：`AGPL-3.0-or-later`；
- 项目原创规则数据、方法文档与非软件知识结构：`CC-BY-SA-4.0`；
- 第三方内容：保留原许可证和 NOTICE。

负责人仍须确认版权/署名主体、CC 适用目录和品牌/商标边界。候选许可证文件存在，不等于
授权已经生效。

### 2. Git 历史邮箱元数据

全历史审计基线共有 126 个提交，其中 20 个提交使用非 GitHub `noreply` 邮箱。封卷
Manifest 只记录数量，不复制邮箱值。PR CI 产生但不会进入真实分支的临时合并提交不计入
公开历史；所有真实 Git refs 仍纳入扫描。直接把现仓库设为 Public 会公开这些历史元数据。

可选处置必须由负责人决定：

1. 明确接受历史邮箱公开；
2. 书面授权一次性历史重写和受控强推，并接受全部 Commit SHA 改变；
3. 书面授权创建不含旧 Git 历史的公开发布仓库/快照，私有工程仓库继续保留。

当前约束禁止 Codex 自行重写历史、强推或创建第二仓库，因此本项是硬阻断。

### 3. 人工、版权与法律边界

- restricted/sealed、灌顶和口传边界仍需有资格的人复核；工程扫描只能证明仓库未含全文。
- 公共人物隐私、婚恋数据和敏感推断仍需法律/隐私审查；原始数据不随代码仓库公开。
- 产品负责人应人工确认 Demo、Fixture 与截图没有真实身份映射。
- VedAstro 与 DreamBank 的原始数据再分发继续禁止；本次公开范围不包含这些原始文件。

## 状态判断

```text
ENGINEERING_RC_READY=true
AI_HANDOFF_READY=true
NEW_MACHINE_HANDOFF_READY=true
OPEN_SOURCE_ENGINEERING_CLOSURE_READY=true
OPEN_SOURCE_READY=true
PUBLIC_RELEASE_AUTHORIZED=true
```

结论：原始工程封卷所列权利人决定已经闭环。当前公开载荷不声称获得传承审校或法律意见，
而是排除了会触发这些专业审查的内容和默认功能；未来扩大范围时相应门禁自动恢复。

为缩短人工闭环，待签事项已经整理为
[公开发布授权与复核包](public-release-authorization-packet.md)，实际切换顺序与不可逆风险见
[GitHub Public 切换运行手册](public-switch-runbook.md)。这些文件只准备证据和流程，不表示
许可证、商标政策或 Public 授权已经生效。
