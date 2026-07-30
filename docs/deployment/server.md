# 单服务器部署

## 结构

```text
Internet :80/:443
        │
      Caddy
        │ internal network
       Web ── API ── PostgreSQL
                 └── optional DeepSeek egress
```

PostgreSQL 没有宿主机端口映射。Caddy 自动将 HTTP 跳转到 HTTPS，并管理证书。
防火墙只开放 80/443 和受限管理 SSH；数据库端口不开放。

## 配置

在服务器 Secret Manager 或仅所有者可读的 `.env` 中配置：

- `APP_ENV=production`
- `PUBLIC_ORIGIN=https://<domain>`
- `SESSION_COOKIE_SECURE=true`
- 生成的数据库密码、32 字节字段加密密钥和一次性所有者口令
- `DOMAIN`
- 可选 `DEEPSEEK_API_KEY`

不要在仓库写入域名、IP、密码或证书。生产配置缺失或弱时 API 会拒绝启动。

## 启动

```bash
docker compose -f docker-compose.yml -f docker-compose.server.yml up -d --build
docker compose ps
curl -fsS https://<domain>/api/health
curl -fsS https://<domain>/api/ready
```

升级前先备份。升级使用普通 Git 快进、重新构建、执行幂等 migration，再检查
Health、Ready、登录、三际录和代表性 Replay。失败时回到上一应用 Commit 并恢复
升级前备份；不要改写 migration 历史。

建议设置容器日志轮转、磁盘 80% 告警、备份保留检查，并按实际主机容量配置
`DB_POOL_MAX`。Caddy 限制请求体 10MB、头部读取 10 秒和响应 60 秒。
