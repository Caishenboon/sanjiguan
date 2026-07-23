# DeepSeek Provider 核查记录

核对日期：2026-07-23。

官方资料显示当前模型标识为 `deepseek-v4-flash` 和 `deepseek-v4-pro`；旧
`deepseek-chat`、`deepseek-reasoner` 将于 2026-07-24 停用。本次受控测试默认使用
`deepseek-v4-flash`，仍可通过手动 workflow input 覆盖。

依据：

- https://api-docs.deepseek.com/guides/function_calling/
- https://api-docs.deepseek.com/quick_start/pricing
- https://api-docs.deepseek.com/guides/json_mode/
- https://api-docs.deepseek.com/api/list-models

审计结论：

- Base URL、模型、超时、重试、max tokens 和请求上限均为服务端配置。
- Key 只从 `DEEPSEEK_API_KEY` 读取；无前端变量。
- 仅 429/5xx、网络/超时或 Schema 失败允许有限重试；有熔断和模板回退。
- JSON Output 开启；返回对象通过严格 allowlist，不接受锁定字段。
- 发送字段由显式 allowlist 重建，而非依赖删除黑名单。
- 不记录 Prompt、原始响应、Authorization Header 或供应商堆栈。
- 供应商失败对外归一化为非敏感错误类型。
- 普通 CI 继续使用 Fake Provider，不读取 Repository Secret。
