# 三际观 V1 Release Candidate 交付说明

状态：`1.0.0-rc.1` 候选，仓库保持 Private，未创建 Tag 或 GitHub Release。

## 产品闭环

V1 将邀请制进入、主体原始出生记录、六类记录、实物三钱、八字/紫微/六爻固定研究
Profile、六象合参、宿世观、中阴观、缘契观、命势长图、确定性三际断章、三际录、
Replay、Reanalysis、Compare、导出和删除接到真实 API 与 PostgreSQL。浏览器状态不是档案或
执行历史的权威来源。

Owner 可以签发 1–168 小时的一次性 Member/Viewer 邀请。服务端仅存令牌哈希；管理员
研究路由仍为 Owner-only，普通成员通过主体范围路由运行自己的固定研究 Profile。

## 传统体系完成度

- 八字：固定 `bazi-ziping-complete-v1@1.0.0` 研究 Profile，输出四柱、藏干、十神、
  五行结构、月令、通根、旺衰证据、格局/调候/用神候选以及大运、流年、流月机械结构。
- 紫微：固定 `ziwei-sanhe-complete-v1@1.0.0` 受限三合研究 Profile，要求人工确认农历输入
  和闰月标记；展示十二宫、命身宫、五行局、主辅煞曜、四化、三方四正和周期结构。
- 六爻：实物三钱以 2/3 为规范输入，展示本卦、动爻、变卦、八宫、纳甲、世应、六亲、
  六神、飞伏、旬空、月日关系、进退/反伏吟候选和用神候选。

以上全部是 `research_active / UNCONFIRMED / production_activatable=false`；不代表所有门派
共识。六象融合为 `sanji_original`。

## AI 边界

三际枢在无 `DEEPSEEK_API_KEY` 时仍生成完整结构与确定性报告。DeepSeek 只能接收最小化、
结构化摘要并润色白名单字段；姓名、排盘、分数、排名、吉凶、应期、证契、逆证及所有
Hash均锁定。Schema、白名单或锁字段校验失败时整份模型输出被拒绝并回退模板。

本地验收未读取或调用真实 DeepSeek 密钥。可选真实 Smoke 只允许手动工作流、虚构数据和
Repository Secret，并须由产品负责人明确触发。

## 数据主权与安全

- 原始出生记录完整加密保存；未知值不补造，经纬度必须由用户明确提供。
- 三际录、执行输入、结果和版本进入 PostgreSQL；敏感正文不写日志或 Trace。
- 私人表启用 FORCE RLS；应用角色无表所有权、超级用户和 BYPASSRLS。
- 导出含 Manifest、版本和 Hash；软删除、彻底删除及 Replay 不可用语义明确。
- PWA 只缓存公共壳层资产，排除 API、主体、记录、合参、三际录和设置路径。

## 部署与恢复

主启动路径：

```bash
python scripts/init_env.py
docker compose up --build
```

PostgreSQL 不发布主机端口；Web 只绑定 `127.0.0.1:3000`。本地原生 PostgreSQL 16.14
已从空库执行 24 条 migration，并完成虚构 Demo、确定性回退、Replay/Reanalysis、备份和
全新空库恢复。Docker 冷启动由远程 `v1-release-gates` 在干净 Ubuntu runner 验收。

## 许可证与公开边界

当前 `LICENSE` 不授予公开许可。候选方案为：原创代码 AGPL-3.0-or-later；原创规则数据、
方法文档与非软件知识结构 CC BY-SA 4.0。第三方资产遵守各自许可；Restricted、Sealed、
授权不明和不可再分发正文不得进入公开仓库。最终许可与公开必须由产品负责人书面批准。

## 验收证据

- 冷启动记录：`docs/releases/evidence/v1-rc-cold-start.redacted.txt`
- 恢复记录：`docs/releases/evidence/v1-rc-backup-restore.redacted.txt`
- 测试统计：`docs/releases/evidence/v1-rc-test-summary.json`
- 安全审计：`docs/releases/v1-rc-security-audit.md`
- 响应式截图：`docs/releases/evidence/screenshots/`

远程 PR、CI Run、最终提交和跨平台结果在 PR 验收完成后补入本文件；PR 保持 Open。
