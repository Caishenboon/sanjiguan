# V1 RC 视觉证据

这些截图由 `apps/web/tests/evidence/v1-rc-evidence.spec.ts` 在本机隔离测试服务器中生成，
只使用测试中声明的完全虚构响应。它们不是 Playwright 视觉 Golden，也不会替代双平台视觉
回归基线。生成过程未读取真实用户资料、外部完整研究数据或 DeepSeek Secret。

| 文件 | 视口/裁切 | 真实页面 | 验收内容 |
| --- | --- | --- | --- |
| `v1-rc-report-desktop-1440.png` | 1440 桌面整页 | `/consult/life-trend` | 命势长图与三际断章 |
| `v1-rc-life-trend-tablet-768.png` | 768 平板整页 | `/consult/life-trend` | 命势长图、文字表格回退与报告 |
| `v1-rc-sushe-wide-1920.png` | 1920 宽屏整页 | `/consult/sushe` | 宿世候选、认识状态与资料不足标记 |
| `v1-rc-onboarding-mobile-390.png` | 390 手机整页 | `/profile/new` | 完全虚构主体立卷、未知时刻与确认边界 |
| `v1-rc-insufficient-liuxiang-1440.png` | 1440 桌面整页 | `/consult/liuxiang` | 六象零证据及“资料不足，暂不成断” |
| `v1-rc-deterministic-report-no-ai-1440.png` | 报告组件裁切 | `/consult/life-trend` | DeepSeek 路由调用数为 0 时的确定性模板报告 |

每个文件的实际尺寸、SHA-256、数据分类和 Provider 调用计数记录在
[`v1-rc-visual-evidence.json`](../v1-rc-visual-evidence.json)。

人工复核结论：六张图片均为现有页面真实渲染；未发现真实身份、真实出生资料、Token、
密钥、本机绝对路径或受限知识内容。截图只证明 RC 页面可运行、状态可见和响应式呈现，
不证明术数规则的现实有效性。
