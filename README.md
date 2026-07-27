# 三际观——宿世因缘与命势推演系统

内部工程名继续使用 `samsara-engine`。确定性核心位于 `packages/sanji-engine`；
八字、紫微与实物三钱已有 Owner-only、可回放的确定性机械研究引擎；
其生产规则仍未激活。解释性易经、密宗、中阴、宿世身份、因缘评分和
命势 K 线继续禁用。八字与紫微必须显式选择研究 Profile，不存在默认
方法；所有解释层均为空。

## API

```bash
python -m venv work/.venv
work/.venv/Scripts/python -m pip install -r apps/api/requirements.txt
work/.venv/Scripts/python -m uvicorn apps.api.app.main:app --reload
```

内存适配器只用于单元测试和本地快速演示，并且必须显式设置
`STORAGE_BACKEND=memory`；未声明 backend 不会自动回退。`APP_ENV=production`
时内存适配器会拒绝启动。

真实 PostgreSQL 测试模式：

```bash
set APP_ENV=test
set STORAGE_BACKEND=postgres
set KEY_PROVIDER=test-only
set TEST_ENCRYPTION_KEY_HEX=<64 hex test-only key>
set DATABASE_URL=postgresql://.../sanjiguan_test
work/.venv/Scripts/python -m uvicorn apps.api.app.postgres_app:app
```

该入口实现邀请、会话和 Profile CRUD 的 HTTP→PostgreSQL 链路。测试 key
provider 在生产环境被拒绝。
PostgreSQL 16 migration：

```bash
set DATABASE_URL=postgresql://migration_owner:...@localhost/sanjiguan
work/.venv/Scripts/python scripts/migrate.py
```

生产数据库凭据和加密密钥必须由 Secret Manager/KMS 注入。仓库中的测试 key
provider 明确禁止在生产环境使用。

## Web

```bash
cd apps/web
pnpm install --frozen-lockfile
pnpm build
pnpm dev
```

共享设计系统与组件故事：

```bash
cd packages/sanji-ui
pnpm install --frozen-lockfile
pnpm build-storybook
```

External Oracle 仅用于合成/批准数据的差分研究，不进入 Engine Hash，
也不允许生产调用。固定版本与许可证见 `third-party-lock.json`。

## 验收

```bash
work/.venv/Scripts/python -m unittest discover -s tests -p "test_*.py"
work/.venv/Scripts/python -m unittest discover -s apps/api/tests -p "test_*.py"
work/.venv/Scripts/python scripts/validate_sprint1a5.py
work/.venv/Scripts/python scripts/validate_sprint1a6.py
work/.venv/Scripts/python scripts/validate_sanji_engine.py
work/.venv/Scripts/python scripts/validate_bazi_method_foundation.py
work/.venv/Scripts/python scripts/validate_ziwei_oracle_ui.py
work/.venv/Scripts/python scripts/check_doc_links.py
```

真实 PostgreSQL 16 测试需要 `TEST_DATABASE_URL`；CI 会从空库执行全部 migration、
重复迁移、RLS/授权/撤权和并发幂等测试。
