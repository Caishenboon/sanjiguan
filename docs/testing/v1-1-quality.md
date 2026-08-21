# V1.1 质量验证

## 本地门禁

```bash
python scripts/validate_v1_1_quality.py
python scripts/validate_v1_ux_evidence.py
python scripts/check_product_language.py
python scripts/validate_handoff.py
python scripts/check_secrets.py
python scripts/check_portability.py
python scripts/check_doc_links.py
cd apps/web && pnpm build && pnpm test:visual
```

完整 CI 继续执行 Python、API、PostgreSQL 16、RLS、HTTP→PostgreSQL、Engine 跨平台确定性、Web build、Storybook、Playwright、Ubuntu/Windows 视觉、Lighthouse、Gitleaks、许可证、SBOM、备份恢复、Manifest、17 个 Hash 与 V1 release gates。

## 判定规则

- 必要检查不得 skip、`continue-on-error` 后伪装成功或降低阈值。
- 视觉失败先查看 actual、expected、diff；只更新已人工确认的平台和页面。
- 本轮不调用真实 DeepSeek。Evidence manifest 中每张图的 Provider 调用数必须为 0。
- CI 不依赖实时外部研究数据；所有体验证据使用完全虚构数据。
- 只有 GitHub 上最新 PR Commit 的全部 Job 成功后，才可评估自动合并门槛。

## 已知环境边界

Windows 本地可验证 production build、Playwright 和 Windows snapshot。Ubuntu snapshot 与 Lighthouse 的权威证据来自固定 GitHub Actions 环境；不得用 Windows 输出覆盖 Linux 基线。
