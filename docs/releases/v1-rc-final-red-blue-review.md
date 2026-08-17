# V1 RC 最终红蓝审查

审查对象为私有仓库 PR #26 的 `1.0.0-rc.1` 工程候选。本审查只判断工程封卷、AI交接、
换机交接、合并和公开边界，不判断术数现实有效性，也不授权生产规则激活、公开、Tag 或
Release。证据基线为提交 `96b89d5f2e784bf414e9f97b7f02f81794285c45` 与
[CI Run 31998530992](https://github.com/Caishenboon/sanjiguan/actions/runs/31998530992)。

## 红队风险

| 等级 | 风险 | 证据与影响 | 当前处置 |
| --- | --- | --- | --- |
| P0 | 无已知工程合并阻断项 | CI 6/6，0 failed、0 skipped；冷启动、恢复、RLS、Secret Scan 与双平台确定性通过 | 保持 PR Open，等待负责人授权 |
| P1 | 规则仍为研究态 | 所有传统与三际原创规则仍为 `UNCONFIRMED` 且不可生产激活；误读会把研究候选当事实 | UI/报告保留 research-only 与认识状态；公开前需专家审校 |
| P1 | 许可证与知识再分发未闭环 | 根 LICENSE 不授予公开许可；VedAstro、知识全文、restricted/sealed 边界仍需人工/法律核验 | 阻止公开，不阻止私有工程合并 |
| P1 | AI交接时可能越权 | 新维护者若绕过 Schema、锁字段或最小摘要，可能让成文层污染结构结论或泄露正文 | DeepSeek不在核心；校验失败整份回退；交接文档要求先读边界 |
| P1 | 新电脑生产配置错误 | 默认/弱密钥、错误域名、未恢复数据库或复制旧 SSH 私钥会破坏安全与可用性 | 生产配置 fail-closed；提供独立 Windows/Linux 换机步骤与恢复演练 |
| P1 | 私人页面被爬虫或缓存 | 登录后页面若失去 `noindex`、`no-store` 或服务工作线程排除，可能泄漏私人路径和正文 | CI独立验证私人路由、响应缓存和 PWA 排除；公开前还需真实域名复核 |
| P2 | 部分本地工具差异 | Windows 本地 Lighthouse/容器能力可能受 Chrome、Docker 或权限影响 | Ubuntu CI 为权威；本地失败不得伪装成通过 |
| P2 | 视觉证据不是长期 Golden | 封卷截图证明页面和状态存在，但不覆盖所有浏览器、字体或真实数据规模 | 双平台视觉回归仍为独立门禁；截图清单固定尺寸和 Hash |
| P2 | AI供应商输出不可重复 | 外部模型相同输入不保证逐字一致 | 核心 Hash 与叙事 Hash 分离；历史保存原响应；无密钥有确定性回退 |

## 蓝队优势

- `sanji-engine` 是唯一确定性核心；Web、API 与 DeepSeek 层不得复制评分或排盘规则。
- Engine、Ruleset、Policy、Profile、输入快照、Trace 与 Hash 支持原版本 Replay；Reanalysis
  新建记录而不覆盖历史结果。
- Windows/Linux 确定性、PostgreSQL 16 migration/RLS/E2E、Web/Storybook/视觉/Lighthouse、
  Gitleaks 和冷启动恢复均在同一远程门禁真实执行。
- 无 `DEEPSEEK_API_KEY` 仍能完成结构化结果和完整确定性报告；Provider 失败或越权即整份
  回退，不影响核心 Hash。
- Docker 默认不公开 PostgreSQL，生产配置拒绝弱密钥与不安全 Cookie；私人正文不进入日志。
- 备份恢复、导出/删除、换机与新环境步骤已有机器证据；仓库不包含运行数据库或真实资料。
- 视觉证据由现有路由、真实组件和合成 API 响应生成，没有用静态拼图冒充页面。

## 阻止合并项

当前未发现 P0 或其他必须阻止 PR #26 工程合并的项目。此前缺失的远程 CI 明细、两次失败
原因、红蓝审查和六项新增视觉证据均已补齐并加入机器校验。合并仍必须由项目负责人明确
授权；此结论本身不是合并授权。

## 只阻止公开、不阻止私有合并项

1. 正式代码许可证与规则/知识数据许可证尚未书面决定。
2. restricted/sealed、灌顶/口传及知识全文再分发边界尚需合格人工复核。
3. VedAstro 等外部数据的再分发许可、版权和来源条件尚未闭环。
4. 公共人物隐私、敏感推断和在世人物保护需要法律审查。
5. Git 全历史还需公开前最终人工复核；自动 Gitleaks 成功不能替代法律/版权判断。
6. 产品负责人尚未书面授权 Public、Tag 或 Release。

## AI交接风险

- 维护者必须先阅读 `docs/handoff/decision-boundaries.md`，不得把 DeepSeek 接入机械计算、
  Evidence、权重、状态、吉凶、应期或 Hash。
- Prompt、Provider、模型和预算可以配置，但真实 Secret 只能从后端环境变量读取；不得在
  文档、日志、测试夹具或远程 URL 中保存。
- 梦境、关系、日记全文和完整出生地址不属于默认可发送摘要。任何扩大字段范围都需独立
  隐私审查。
- AI响应只有同时通过 Schema、白名单和锁字段比较才可保存；失败必须使用确定性模板，
  不能部分采纳。

## 新电脑部署风险

- GitHub只保存代码，不保存 PostgreSQL 数据、`.env`、KMS材料或备份密钥；换机必须单独
  恢复加密备份和私人配置。
- SSH 私钥不得复制到新设备；应重新生成并由账户所有者授权。
- 恢复必须在空环境执行，并核验 migration 版本、三际录、Replay 与保护 Hash；不能把仍在
  运行的原数据库当成恢复成功证据。
- 生产域名、HTTPS、备份保留、数据地区、KMS和删除 SLA 仍需部署负责人确认。

## 爬虫与私人页面风险

- `robots.txt`、`llms.txt` 与公开说明只服务于公开元数据，不授权爬取私人页面或 API。
- `/profile`、`/records`、`/consult`、三际录与设置页面必须继续 `noindex`、`no-store`，且不
  被 Service Worker 缓存；真实反向代理也必须保留这些响应头。
- 任何未来的公开首页不能链接可枚举的私人对象 ID，也不能将研究详情、Trace 或正文嵌入
  静态页面。

## 许可证和知识再分发风险

- 根 `LICENSE` 当前是保留权利说明，不得误读为 AGPL 或 CC 已正式生效。
- 代码许可、原创规则数据、方法文档、知识内容、字体/图片和外部数据必须分别治理。
- Restricted/Sealed 内容不得摄入、嵌入或转述为操作步骤；来源不清的内容只能保存书目信息。
- 自动 SBOM 与依赖 Notice 不能替代对知识全文、译本、图片和数据集许可的逐项人工判断。

## 最终六项状态判断

| 状态 | 判断 | 理由 |
| --- | --- | --- |
| `ENGINEERING_RC_READY` | `true` | 远程 6/6、冷启动、恢复、RLS、双平台与安全门禁通过 |
| `AI_HANDOFF_READY` | `true` | AI边界、无密钥回退、锁字段与交接入口已经固化 |
| `NEW_MACHINE_HANDOFF_READY` | `true` | Windows/Linux步骤、备份恢复和配置边界已有验证 |
| `MERGE_READY` | `true` | 本轮证据缺口闭环；无已知 P0，仍等待负责人授权 |
| `OPEN_SOURCE_READY` | `false` | 许可证、知识版权、外部数据和法律审查未完成 |
| `PUBLIC_RELEASE_AUTHORIZED` | `false` | 未收到项目负责人书面公开、Tag 或 Release 授权 |

结论：PR #26 可进入负责人最终合并决策；仓库必须继续 Private，PR 保持 Open，不创建 Tag
或 Release，不调用 DeepSeek，不将研究态规则写成生产共识。
