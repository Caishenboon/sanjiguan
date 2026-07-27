# 视觉回归确定性规范

## 权威环境

GitHub Actions `baseline` job 是唯一权威视觉回归环境。它固定使用
`ubuntu-24.04`、仓库锁定的 Playwright/Chromium、`C.UTF-8`、UTC 和
仓库依赖提供的字体。操作系统、浏览器或字体版本变化都必须作为显式
基线变更审查，不得静默接受。

`apps/web/tests/visual/__screenshots__/linux/` 保存权威 Linux 基线。
`win32/` 只用于 Windows 本地反馈；两类图片不得互相覆盖，也不得用
Windows 结果更新 Linux 权威基线。

## 字体

网页从锁定的 Fontsource `5.3.0` 包加载：

- Noto Sans SC；
- Noto Serif SC；
- Noto Sans Mono。

三个字体包均声明 `OFL-1.1`，版本和用途登记在
`third-party-lock.json` 与 `THIRD_PARTY_NOTICES.md`。字体由包管理器
在构建时取得，字体二进制不直接提交到仓库。视觉测试在截图前等待
`document.fonts.ready`，并检查三个字体均可用；缺失时直接失败，禁止
落入不确定的系统字体。

## 本地验证

在 `apps/web` 中执行：

```text
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
pnpm build
pnpm test:visual
```

Playwright 通过 `{platform}` 自动选择本机目录。Windows 开发者只验证
`win32` 基线。Linux 开发者的结果只有在与 CI 的 Ubuntu、Chromium、
字体和 locale 完全一致时，才可作为 Linux 候选。

`pnpm test:visual:update` 只生成当前平台候选。更新后必须逐张检查，不得
在普通 CI 中使用 `--update-snapshots`。

## 权威基线更新

1. 在固定 CI 环境中生成候选图片。
2. 下载 CI 的 visual-regression Artifact。
3. 人工检查 expected、actual 和 diff。
4. 确认变化来自批准的 UI 修改，而不是字体、浏览器、viewport 或环境漂移。
5. 将审核后的 Linux 图片作为独立提交写入 `linux/`。
6. 重新运行完整 CI。

任何浏览器、Playwright、字体、runner 或截图策略升级，都必须在 PR 中
说明版本变化和视觉影响。

## 失败证据

视觉步骤失败时，CI 保留 14 天 Artifact，其中包含：

- actual screenshot；
- expected screenshot；
- diff screenshot；
- Playwright error context。

视觉步骤采用 `continue-on-error` 仅为收集证据并继续执行 Lighthouse 和
Gitleaks；job 末尾仍会强制失败，不能形成假绿。

禁止直接提高 `maxDiffPixelRatio`、扩大像素阈值或自动接受快照来绕过
差异。阈值变更必须单独论证，并证明不会掩盖真实布局或可读性回归。
