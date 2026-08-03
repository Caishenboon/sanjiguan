# 换电脑迁移

1. 在新电脑安装 Git、Docker 和 Docker Compose。
2. 从 Private GitHub 仓库克隆代码。GitHub 保存代码，不保存运行数据库。
3. 从安全渠道恢复 `.env` 私人配置，不从 Git 恢复密钥。
4. 将加密备份和独立密钥安全移到新电脑。
5. 启动空环境并用 `scripts/restore.py` 恢复数据库。
6. 运行 migration，检查 `/health`、`/ready`、三际录、Replay 和 Hash。
7. 重新配置 `DEEPSEEK_API_KEY`；无密钥时确定性报告仍可用。
8. 在新电脑重新生成 Git SSH 密钥并添加公钥，不复制旧私钥。
9. 验收完成后，按保留政策安全处置旧电脑上的明文临时文件。

如果彻底删除过敏感快照，对应历史条目应显示 `replay_unavailable`，不得从缓存或
旧日志伪造恢复。
