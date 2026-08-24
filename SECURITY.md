# Security policy

本项目当前为 Private V1 候选。请通过 GitHub Private 仓库的安全报告渠道联系项目
所有者，不要在 Issue 中提交漏洞细节、私人资料或密钥。未来仓库获准公开时，必须先启用
GitHub Private Vulnerability Reporting；公开 Issue 仍只用于不含敏感细节的普通缺陷。

## 支持范围

仅最新 `main` 和当前开放的 V1 发布候选分支接受安全修复。研究规则的文学质量问题
不是安全漏洞；越权、RLS 绕过、密钥泄漏、私人正文日志泄漏、AI 修改锁定字段和
Replay 伪造属于安全问题。

## 密钥

- `DEEPSEEK_API_KEY`、数据库密码、字段加密密钥和初始化口令只从环境或 Secret
  Manager 注入。
- 生产启动会拒绝测试 Key Provider、HTTP 公网 Origin、不安全 Cookie 和弱配置。
- 新电脑重新生成 Git SSH 私钥，不复制旧私钥。
- 不要在报告中粘贴 Token、Cookie、验证码、恢复码或私钥。

## 数据

梦境、关系、出生资料和日记视为敏感私人资料。API 使用真实会话与 PostgreSQL
FORCE RLS；日志只保留请求关联 ID、错误类别和服务状态，不应记录私人正文。

发现疑似泄漏时先撤销相关密钥和会话，再保留最少的脱敏证据用于调查。
