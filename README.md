# 三际观——宿世因缘与命势推演系统

内部工程名继续使用 `samsara-engine`。确定性核心位于 `packages/sanji-engine`；
八字、紫微、解释性易经、密宗、中阴、宿世身份、因缘评分和命势 K 线生产规则均未激活。
八字方法档案与边界案例只用于 Owner 审校，不生成四柱。

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

## 验收

```bash
work/.venv/Scripts/python -m unittest discover -s tests -p "test_*.py"
work/.venv/Scripts/python -m unittest discover -s apps/api/tests -p "test_*.py"
work/.venv/Scripts/python scripts/validate_sprint1a5.py
work/.venv/Scripts/python scripts/validate_sprint1a6.py
work/.venv/Scripts/python scripts/validate_sanji_engine.py
work/.venv/Scripts/python scripts/validate_bazi_method_foundation.py
work/.venv/Scripts/python scripts/check_doc_links.py
```

真实 PostgreSQL 16 测试需要 `TEST_DATABASE_URL`；CI 会从空库执行全部 migration、
重复迁移、RLS/授权/撤权和并发幂等测试。
