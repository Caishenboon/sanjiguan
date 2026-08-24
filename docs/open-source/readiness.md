# 开源准备状态

仓库必须继续保持 **Private**。PR #27 已以普通 Merge Commit 合并，合并后
[main CI Run 32705480100](https://github.com/Caishenboon/sanjiguan/actions/runs/32705480100)
六项检查全部成功。V1 私人运行不受许可证待决定项阻断，但任何公开、Tag、Release
或算法包发布都必须等待产品所有者书面批准。

- [x] Git 全历史 Secret Scan 完成；[CI Run 31998530992](https://github.com/Caishenboon/sanjiguan/actions/runs/31998530992)
  的 Gitleaks 与 Secret Scan 未发现待处理泄漏
- [x] 当前 Git 跟踪内容通过私人数据、敏感测试数据、绝对路径与 Secret 机器扫描；证据见
  [安全审计](../releases/v1-rc-security-audit.md)
- [x] 机器确认仓库未跟踪 restricted/sealed 全文、现代译文或具体修法步骤；证据见
  [开源发布封卷](public-release-closure-v1.md)
- [ ] 由合格传统/传承审校人复核 restricted/sealed、灌顶和口传边界
- [ ] 复核知识库全文、译本、图片和注疏版权
- [x] 生成第三方依赖清单和机器可读 SBOM；证据见 `sbom.cdx.json` 与
  [许可证审计](license-audit-v1-rc.md)
- [x] 准备代码与原创知识资产候选许可证；正式激活仍待书面决定
- [x] README、SECURITY.md、CONTRIBUTING.md 和 NOTICE 草案
- [x] 隐私、导出、删除、备份与部署说明；冷启动及恢复证据见
  [V1 RC交付说明](../releases/v1-rc-delivery.md)
- [x] 机器核验 26 张截图 Manifest 均标记为完全虚构，文件 Hash 一致且无 Provider 调用
- [ ] 产品负责人逐项人工确认 Demo/Fixture/截图没有真实身份映射
- [x] GitHub Actions 默认最小权限 `contents: read`
- [x] DeepSeek 仅由后端环境变量 `DEEPSEEK_API_KEY` 注入
- [x] 当前公开代码范围排除 VedAstro 原始数据和 Fixture，Manifest 保持不可提交、不可再分发
- [ ] 若未来分发 VedAstro 数据，另行完成两个固定 Revision 的再分发许可审查
- [ ] 获得 DreamBank 正文再包装的书面许可；此前 Connector 保持禁用
- [ ] 复核三际观原创六象和 Mapping 规则的数据许可证
- [ ] 完成公共人物隐私、敏感推断和在世人物保护法律审查
- [ ] 决定 20 个非 GitHub noreply 历史提交邮箱的公开处置方式
- [ ] 确认版权/署名主体及品牌、商标边界
- [ ] 产品所有者书面批准公开
- [x] 已准备逐项签署的[公开发布授权与复核包](public-release-authorization-packet.md)
- [x] 已准备[Public 切换运行手册](public-switch-runbook.md)，其中要求切换后立即配置 `main` 保护与私密漏洞报告
- [x] 已准备保守的[`TRADEMARKS.md`](../../TRADEMARKS.md)候选文本；尚未生效

许可证候选为代码 AGPL-3.0-or-later、原创规则数据与方法文档 CC BY-SA 4.0。
根 `LICENSE` 明确不在负责人批准前授予公开许可。不得因仓库中存在依赖许可证而
推定三际观自身已经授权公开。

当前状态必须同时保持：

```text
ENGINEERING_RC_READY=true
AI_HANDOFF_READY=true
NEW_MACHINE_HANDOFF_READY=true
OPEN_SOURCE_ENGINEERING_CLOSURE_READY=true
OPEN_SOURCE_READY=false
PUBLIC_RELEASE_AUTHORIZED=false
```

机器检查完成只说明私有工程候选满足相应门禁。待确认项及选择见
[公开发布待确认决定](publication-decisions.md)，机器证据见
[`public-release-manifest.json`](public-release-manifest.json)。人工 Demo/Fixture 复核、
传统/传承审校、历史邮箱处置、版权与法律审查、许可证决定以及负责人公开授权仍未完成，
不能被自动扫描替代。
