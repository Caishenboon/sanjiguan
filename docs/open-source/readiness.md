# 开源准备状态

项目所有者已于 2026-08-24 授权公开。开源封卷 PR #28 已以普通 Merge Commit 合并，
[main CI Run 32721037735](https://github.com/Caishenboon/sanjiguan/actions/runs/32721037735)
六项检查全部成功。当前状态为“许可证已激活、公开切换已授权、等待最终 Public 操作”；
Tag、GitHub Release、规则生产激活与外部数据 Connector 仍未授权。

- [x] Git 全历史 Secret Scan 完成；[CI Run 31998530992](https://github.com/Caishenboon/sanjiguan/actions/runs/31998530992)
  的 Gitleaks 与 Secret Scan 未发现待处理泄漏
- [x] 当前 Git 跟踪内容通过私人数据、敏感测试数据、绝对路径与 Secret 机器扫描；证据见
  [安全审计](../releases/v1-rc-security-audit.md)
- [x] 机器确认仓库未跟踪 restricted/sealed 全文、现代译文或具体修法步骤；证据见
  [开源发布封卷](public-release-closure-v1.md)
- [x] 当前公开范围通过 fail-closed 检查：不含 restricted/sealed、灌顶/口传正文、现代译文全文或修法步骤；未来扩大范围仍需合格审校
- [x] 当前知识资产只有三际原创研究结构与书目/访问边界，不分发现代译文、扫描、图片或注疏全文
- [x] 生成第三方依赖清单和机器可读 SBOM；证据见 `sbom.cdx.json` 与
  [许可证审计](license-audit-v1-rc.md)
- [x] 已激活原创软件 AGPL-3.0-or-later 与原创规则/方法/非软件知识结构 CC BY-SA 4.0
- [x] README、SECURITY.md、CONTRIBUTING.md 和 NOTICE 草案
- [x] 隐私、导出、删除、备份与部署说明；冷启动及恢复证据见
  [V1 RC交付说明](../releases/v1-rc-delivery.md)
- [x] 机器核验 26 张截图 Manifest 均标记为完全虚构，文件 Hash 一致且无 Provider 调用
- [x] 产品负责人接受 26 项 synthetic Manifest、文件 Hash、Provider=0 与安全扫描封卷
- [x] GitHub Actions 默认最小权限 `contents: read`
- [x] DeepSeek 仅由后端环境变量 `DEEPSEEK_API_KEY` 注入
- [x] 当前公开代码范围排除 VedAstro 原始数据和 Fixture，Manifest 保持不可提交、不可再分发
- [x] VedAstro 两个 Connector 在公开版本中默认禁用；未来启用或分发须另行许可/隐私审查
- [ ] 获得 DreamBank 正文再包装的书面许可；此前 Connector 保持禁用
- [x] 三际观原创六象、Mapping 规则和非软件方法资产采用 CC BY-SA 4.0
- [x] 当前公开范围不包含公共人物原始数据、Fixture 或敏感推断，Connector 默认禁用；扩大范围前法律/隐私审查仍为硬门禁
- [x] 产品所有者接受公开切换时 21 次非 GitHub noreply 历史邮箱出现（1 个唯一邮箱值）公开，不重写历史；第 21 次来自 PR #29 普通 Merge Commit，未引入新的邮箱值
- [x] 版权/署名主体为 Caishenboon（2026），品牌采用 `TRADEMARKS.md`
- [x] 产品所有者书面批准将仓库切换为 Public
- [x] 已准备逐项签署的[公开发布授权与复核包](public-release-authorization-packet.md)
- [x] 已准备[Public 切换运行手册](public-switch-runbook.md)，其中要求切换后立即配置 `main` 保护与私密漏洞报告
- [x] 保守的[`TRADEMARKS.md`](../../TRADEMARKS.md)已生效

许可证已激活：项目原创软件采用 AGPL-3.0-or-later；项目原创规则数据、方法文档和
非软件知识结构采用 CC BY-SA 4.0。第三方、私人、外部数据、restricted/sealed 与权利
不清资产明确排除。

当前状态必须同时保持：

```text
ENGINEERING_RC_READY=true
AI_HANDOFF_READY=true
NEW_MACHINE_HANDOFF_READY=true
OPEN_SOURCE_ENGINEERING_CLOSURE_READY=true
OPEN_SOURCE_READY=true
PUBLIC_RELEASE_AUTHORIZED=true
```

授权决定见[公开发布决定记录](publication-decisions.md)，机器证据见
[`public-release-manifest.json`](public-release-manifest.json)。当前不声称具备传统/传承
审校或法律意见；而是通过排除受限内容、外部数据与公共人物结果来限定公开载荷。未来扩大
上述范围时，专业审查会重新成为硬门禁。
