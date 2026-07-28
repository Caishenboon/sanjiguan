# 视觉回归确定性规范

## 权威环境

GitHub Actions 的 `web-visual-determinism` 矩阵是唯一权威视觉回归环境：

- `ubuntu-24.04` 对应 `linux/` Snapshot；
- `windows-2025` 对应 `win32/` Snapshot。

两端均使用仓库锁定的 Node、pnpm、Playwright/Chromium、UTC 和字体依赖。
本地运行只用于预检，不能替代远程矩阵结果。操作系统、浏览器、字体或 Runner
版本发生变化时，必须显式生成候选、检查 Diff 并单独提交，不能静默接受。

Snapshot 目录为：

```text
apps/web/tests/visual/__screenshots__/linux/
apps/web/tests/visual/__screenshots__/win32/
```

两个平台不得交叉覆盖。Linux 结果只能更新 `linux/`，Windows 结果只能更新
`win32/`。

## 字体

网页从锁定的 Fontsource `5.3.0` 包加载：

- Noto Sans SC；
- Noto Serif SC；
- Noto Sans Mono。

三项均采用 `OFL-1.1`，版本和用途登记在 `third-party-lock.json` 与
`THIRD_PARTY_NOTICES.md`。字体二进制由包管理器在构建时取得，不直接提交进
仓库。视觉测试在截图前等待 `document.fonts.ready`，并验证三种字体可用；
缺失时直接失败，禁止落入不确定的系统字体 fallback。

## 本地验证

在 `apps/web` 中执行：

```text
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
pnpm build
pnpm test:visual
```

Playwright 通过 `{platform}` 选择当前系统目录。本地通过只说明当前工作站与
已审核基线一致；合并资格仍以 GitHub Actions 的 Linux 和 Windows 矩阵均通过
为准。

`pnpm test:visual:update` 只生成当前平台的候选。普通 CI 不得执行
`--update-snapshots`。

## Snapshot 更新

1. 在固定 CI 环境生成候选；
2. 下载失败运行的 visual-regression Artifact；
3. 人工检查 actual、expected、diff 和 error context；
4. 排除字体、浏览器、viewport、动态时间、API 或后端错误导致的漂移；
5. 只更新受影响平台和页面；
6. 在独立提交中记录原因和审核依据；
7. 重新运行完整 CI。

任何 Playwright、Chromium、字体、Runner 或截图策略升级，都必须在 PR 中说明
版本变化和视觉影响。

## 失败证据与硬失败

视觉步骤使用 `continue-on-error` 只为继续收集证据。每个平台随后都有
`Enforce visual regression result` 硬门禁，因此失败不能形成绿色 Job。

失败 Artifact 保留 14 天并包含：

- actual screenshot；
- expected screenshot；
- diff screenshot；
- Playwright error context；
- 对应平台的 21 张已审核基线副本。

禁止通过提高 `maxDiffPixelRatio`、扩大像素阈值、删除页面或设备、缩小旗舰页
截图范围或自动接受 Snapshot 来绕过差异。阈值变更必须单独论证，并证明不会
掩盖真实布局或可读性回归。
