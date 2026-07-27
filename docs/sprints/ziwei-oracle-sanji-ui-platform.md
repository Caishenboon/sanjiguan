# 紫微、Oracle 与 Sanji UI 平台 Sprint 交付说明

本 Sprint 在同一分支和同一 PR 中交付三项能力：

1. 两个显式 Profile 的紫微三合基础机械研究引擎；
2. lunar-python、tyme4py、sxtwl 与 iztro 的隔离差分平台；
3. `packages/sanji-ui` 组件、视觉 Tokens、Storybook 与六个旗舰页面。

规则仍为研究态。Oracle 不影响 Engine；页面只调用契约；数据库加法
迁移不回填或伪造旧记录。详细边界见：

- `docs/algorithms/ziwei-mechanical-research.md`
- `docs/architecture/third-party-integration-matrix.md`
- `docs/design/sanji-visual-language.md`

人工审校待办：D-005、两种闰月政策、生年四化逐干表、时辰边界、
公历转农历方法、权威金样例和可用辅星范围。完成前不得晋升
`production_active`。

## 验收矩阵

- 紫微：12 月 × 12 时辰、五行五局、十四主星、闰月双 Profile、Trace、
  Replay、撤销规则与跨平台固定哈希。
- Oracle：10 个八字边界类 × 3 个 Profile × 3 个 Oracle，共 90 个组合；
  iztro 另以完整十四主星的虚构盘执行标准化差分。
- 回归：八字 420 个机械检查点、74 个合成边界资产、三钱 4096 状态、
  Signals/Inference 30/30。
- 数据：PostgreSQL 16 空库迁移、重复迁移、RLS、并发与 HTTP→PostgreSQL
  E2E。
- 界面：19 个共享组件、14 个 Story、六个旗舰页面、21 张固定 Chromium
  截图及 Lighthouse 四类预算。

## 已知技术债与人工审校

- D-005、闰月、子时、生年四化逐干表、大限方法及权威金样例仍未冻结。
- `source-claims-1.0.0.json` 故意不填写未经确认的传统来源定位；合格审校人
  补齐来源并签署前，规则不得进入生产。
- 自动公历转农历、必要辅星和任何紫微解释均保持关闭。
- sxtwl 在本地 Windows 无可用构建工具时只记录 `unsupported`；Linux CI
  必须安装并实际执行，不能以此例外跳过。
- Storybook/Vite 的大 chunk 警告属于开发工具产物，不进入 Web 生产包；
  后续可拆分 Story 以改善开发加载时间。
- Lighthouse 初始预算为 Performance 0.80、Accessibility 0.90、
  Best Practices 0.90、SEO 0.85，后续提高预算不得删除关键研究警告。
