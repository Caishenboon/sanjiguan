# DeepSeek V1 配置

DeepSeek 仅用于项目所有者明确触发的受控成文。Provider、模型、超时、重试、Token
上限、总请求和预算均通过环境变量配置。核心结构、K线、吉凶、应期、候选、姓名、
支持、逆证与认识状态均锁定。

发送前只形成最小结构摘要，不发送梦境/关系/日记全文、完整出生地址、内部 ID、
Trace 原文或密钥。Schema 或锁字段校验失败、超时、限流和 Provider 失败均使用
确定性成文回退。AI 原文与确定性结果分开保存，可单独删除。

CI 只使用 Mock，不调用付费服务。可选真实 Smoke：

```bash
SANJI_ALLOW_PAID_SMOKE=YES DEEPSEEK_API_KEY=... python scripts/deepseek_v1_smoke.py
```

该命令仅使用固定虚构案例，不是 CI 必需条件。没有实际执行时不得报告已完成真实调用。
