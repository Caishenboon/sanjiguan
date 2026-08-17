# 全新 Windows 电脑安装

本流程不依赖旧电脑路径、数据库口令、DeepSeek 密钥或 Git SSH 私钥。

## 1. 安装与克隆

1. 安装当前受支持的 Git for Windows。
2. 安装 Docker Desktop，并启用 Docker Compose v2。
3. 在 GitHub 为新电脑重新生成 SSH key，或使用 Git Credential Manager；不要复制旧私钥。
4. 将 Private 仓库克隆到任意目录并进入仓库根：

```powershell
git clone <private-repository-url>
cd sanjiguan
```

## 2. 创建本机配置并启动

安装 Python 3.11 或更高版本，然后让脚本生成全新的本机口令和 32 字节加密密钥：

```powershell
python scripts/init_env.py
docker compose up --build
```

脚本只写入被忽略的 `.env`，拒绝覆盖已有文件且不打印密钥。不要从旧电脑复制数据库
密码或 DeepSeek 密钥；如以后启用成文，在新电脑的安全配置中重新设置。

Docker 会先执行 `infra/migrations/`，再启动 PostgreSQL、API 和 Web。打开
`http://127.0.0.1:3000/start`，从本机 `.env` 读取一次性 `OWNER_BOOTSTRAP_TOKEN` 完成首个
Owner。不要把口令粘贴到聊天或日志。

## 3. 虚构验收

在可丢弃的本地环境建立虚构主体、记录和完整分析：

```powershell
python scripts/demo.py create
curl.exe -fsS http://127.0.0.1:3000/api/health
curl.exe -fsS http://127.0.0.1:3000/api/ready
```

在三际录中打开刚生成的条目，执行“按原版本重放”，确认 Hash 匹配。Demo 全部虚构，
不依赖 DeepSeek。需要重置或删除时使用 `python scripts/demo.py reset` 或 `delete`，并按脚本
提示提供当前可丢弃会话。

## 4. 停止、备份、恢复与更新

```powershell
docker compose down
docker compose up -d
docker compose logs -f web api
```

`down` 不删除数据库卷；`docker compose down --volumes` 会不可恢复地清空本地卷，只能在
明确验证目标后执行。备份和空库恢复按
[`../operations/backup-restore.md`](../operations/backup-restore.md) 操作。更新前备份，然后：

```powershell
git fetch origin
git pull --ff-only
docker compose up -d --build
docker compose run --rm migrate
```

最后重新检查 `/health`、`/ready`、三际录和代表性 Replay。
