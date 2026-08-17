# 安装与接续故障排查

## Docker 无法启动

- 先运行 `docker compose config --quiet` 和 `docker compose ps`。
- 查看 `docker compose logs --tail=200 postgres api web`；日志不得粘贴私人正文。
- `/ready` 显示数据库未就绪时，检查 migration 容器是否成功，不要手工跳过 migration。

## 首个 Owner 无法建立

- 确认使用当前电脑 `.env` 中的 `OWNER_BOOTSTRAP_TOKEN`，不要使用旧电脑口令。
- 若已存在 Owner，系统应拒绝再次 bootstrap；通过现有 Owner 签发一次性邀请。
- 不要把口令写入 URL、Issue、PR、聊天或命令历史。

## Replay 不匹配

停止重新分析，记录 Engine、Ruleset、Policy、Profile、输入和数据版本。运行对应历史 Hash
门禁；不得修改旧 Ruleset 或 Golden 让测试通过。彻底删除导致缺少快照时应返回
`replay_unavailable`，不能从缓存伪造恢复。

## 恢复被拒绝

恢复目标必须是空库，Dump SHA-256 必须匹配 Manifest。用新的空数据库重试，不要覆盖
正在运行的数据库。详细步骤见 [`../operations/backup-restore.md`](../operations/backup-restore.md)。

## Web 或视觉测试不稳定

使用固定 Node、pnpm、Playwright 和字体版本；分别使用 Windows/Linux Snapshot。检查失败
Artifact 后只更新确有设计变化的单个平台页面，不提高 diff 阈值。

## GitHub 网络或认证

保持 SSL 校验。HTTPS 不可用时可使用 GitHub 官方 SSH over 443；新电脑重新生成 SSH key。
不要把 Token、私钥、验证码或 Cookie 发到聊天。
