# 三际观

三际观是一个面向少数授权使用者的私人研究工具。V1 将个人记录、易经三钱、
八字与紫微机械结构、六象研究、宿世观、中阴观、缘契观、命势长图、人生 K 线、
三际断章和三际录串成一条可回放、可重新分析的确定性链路。

六象及专题融合属于三际观原创研究体系，不是古代既定算法。相关规则保持
`research_active / UNCONFIRMED / production_activatable=false`。结构化结果由
`packages/sanji-engine` 决定；DeepSeek 可以造景，不能造术。没有 AI 密钥时，
完整确定性报告仍可使用。

仓库目前保持 Private。已准备但尚未激活的候选方案是：原创代码
`AGPL-3.0-or-later`，原创规则数据、方法文档和非软件知识结构 `CC BY-SA 4.0`；
第三方资产保留原许可证。公开、Tag、Release 与正式许可仍须项目所有者书面批准。

## 快速开始

需要 Git、Docker 和 Docker Compose：

```bash
git clone <private-repository-url>
cd sanjiguan
python scripts/init_env.py
docker compose up --build
```

打开 `http://127.0.0.1:3000/start`，使用忽略文件 `.env` 中的
`OWNER_BOOTSTRAP_TOKEN` 完成首次所有者建立。口令只在本机读取，不要粘贴到聊天、
日志或提交记录。

停止与重启：

```bash
docker compose down
docker compose up -d
docker compose logs -f web api
```

`docker compose down` 不删除数据库卷。彻底清理必须显式执行
`docker compose down --volumes`；该操作不可恢复。

## 虚构 Demo

在全新、可丢弃的本地数据库中：

```bash
python scripts/demo.py create
```

Demo 中的主体、地点、梦境、关系和事件全部虚构，不代表现实验证，也不依赖
DeepSeek 或外部完整数据集。

## 运行边界

- 普通用户入口固定为：首页、记录、合参、三际录、我的。
- 研究管理员区受服务端会话和角色门禁保护。
- PostgreSQL 是三际录和执行历史的唯一事实来源；浏览器仅保留未提交草稿与显示状态。
- 原版本 Replay 使用不可变版本和 Hash；彻底删除私人快照后明确返回不可回放。
- AI 不参与排盘、证据、评分、排序、吉凶、应期或 Hash。
- API、Web 与 LLM 层不得复制核心算法。

## 文档入口

- [系统架构](docs/architecture/sanji-engine-contract.md)
- [V1 功能与发布清单](docs/releases/v1-checklist.md)
- [本地和服务器部署](docs/deployment/server.md)
- [备份与恢复](docs/operations/backup-restore.md)
- [换电脑迁移](docs/operations/move-computer.md)
- [导出与删除](docs/privacy/data-export-delete.md)
- [DeepSeek 配置](docs/integrations/deepseek-v1.md)
- [安全说明](SECURITY.md)
- [贡献指南](CONTRIBUTING.md)
- [开源准备状态](docs/open-source/readiness.md)
- [许可证审计](docs/open-source/license-audit-v1-rc.md)
- [知识库公开边界](docs/open-source/knowledge-boundary-v1-rc.md)
- [API 契约](docs/api/openapi.yaml)

## 开发验证

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/validate_v1_release.py
cd apps/web && pnpm install --frozen-lockfile && pnpm build
```

完整 CI 还会运行 PostgreSQL 16、RLS、HTTP→PostgreSQL E2E、Windows/Linux
确定性、视觉回归、Lighthouse、Gitleaks、许可证和 Docker 干净启动门禁。
