# 贡献规范

当前仓库保持 Private。公开贡献流程、代码许可证和规则数据许可证仍需
产品负责人另行书面确认；本文件只记录现阶段工程门禁。

## 视觉测试

- 视觉变更必须运行 Web production build 和 Playwright visual regression。
- GitHub Actions 的固定 Linux 环境是权威基线；Windows 图片只用于本地反馈。
- Linux 与 Windows 快照必须保存在各自平台目录，不得交叉覆盖。
- 基线更新必须独立提交，并附人工审查说明。
- 普通 CI 禁止使用 `--update-snapshots` 自动接受变化。
- 失败时必须检查 actual、expected、diff 和 error context Artifact。
- 不得通过提高像素差异阈值、删除用例或跳过检查来取得绿色结果。

完整流程见 `docs/testing/visual-regression.md`。
