# 贡献规范

当前仓库保持 Private。公开贡献流程、代码许可证和规则数据许可证仍需
产品负责人另行书面确认；本文件只记录现阶段工程门禁。

## 视觉测试

- 视觉变更必须运行 Web production build 和 Playwright visual regression。
- GitHub Actions 的 Linux/Windows 固定矩阵是唯一权威环境；本地结果只用于预检。
- Linux 与 Windows 快照必须保存在各自平台目录，不得交叉覆盖。
- 基线更新必须独立提交，并附人工审查说明。
- 普通 CI 禁止使用 `--update-snapshots` 自动接受变化。
- 失败时必须检查 actual、expected、diff 和 error context Artifact。
- 不得通过提高像素差异阈值、删除用例或跳过检查来取得绿色结果。

完整流程见 `docs/testing/visual-regression.md`。

普通用户页面必须遵守五入口产品主干、白话字段词典和渐进披露边界。不得把
Signal、Mapping、Hash 或合成六象候选放到普通页面首屏，也不得在前端复制
排盘或评分逻辑。路由与旅程说明见
`docs/product/product-spine-user-journey-v1.md`；提交前运行
`python scripts/validate_product_spine_v1.py`。
