# 密钥管理运行约定

1. 立即吊销已暴露的旧 DeepSeek 密钥，并记录在外部安全工单；记录中只保存密钥指纹末 4 位，不保存密钥。
2. 创建新密钥后直接写入部署 Secret Manager 的 `DEEPSEEK_API_KEY`。
3. 本地开发只允许写入被 Git 忽略的 `.env.local`；`.env.example` 永远保持空值。
4. API 启动时验证：provider 为 deepseek 时，密钥、base URL 和模型名必须存在；不得输出其值。
5. 日志过滤字段：`authorization`、`cookie`、`set-cookie`、`api_key`、`token`、原始用户 payload。
6. 每 90 天轮换；泄漏疑似事件立即吊销、重发、扫描提交历史并审计调用记录。
