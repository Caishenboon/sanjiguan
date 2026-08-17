# 全新 Linux 电脑安装

参考环境为受支持的 Ubuntu LTS。安装 Git、Docker Engine、Docker Compose plugin 和
Python 3.11+；使用官方软件源并让当前用户按组织政策获得 Docker 权限。

```bash
git clone <private-repository-url>
cd sanjiguan
python3 scripts/init_env.py
docker compose up --build
```

在新电脑重新生成 Git SSH key，不复制旧私钥。`init_env.py` 会生成新的本机数据库口令、
字段加密密钥和 Owner 引导口令；不要复制旧电脑密码或 DeepSeek 密钥。

打开 `http://127.0.0.1:3000/start`，使用本机 `.env` 中一次性 Owner 口令建立所有者。
随后在可丢弃数据库运行：

```bash
python3 scripts/demo.py create
curl -fsS http://127.0.0.1:3000/api/health
curl -fsS http://127.0.0.1:3000/api/ready
```

确认虚构三际录可见、原版本 Replay 的 Hash 匹配，再按需删除 Demo。

```bash
docker compose down
docker compose up -d
docker compose logs -f web api
```

普通 `down` 保留数据卷。只有明确需要不可恢复清理时才使用
`docker compose down --volumes`。备份、恢复与换机见
[`../operations/backup-restore.md`](../operations/backup-restore.md) 和
[`../operations/move-computer.md`](../operations/move-computer.md)。更新前先备份，再执行
`git pull --ff-only`、重新构建、幂等 migration 和健康/Replay 验证。
