# 系统地图

```text
Web/PWA  apps/web/app + apps/web/components
   ↓ HTTP / versioned JSON
FastAPI  apps/api/app
   ↓
Application Services  apps/api/app/services.py + repositories
   ↓
sanji-engine / 三际枢  packages/sanji-engine/src/sanji_engine
   ├── 时间与历法  calendar/
   ├── 八字        bazi/
   ├── 紫微        ziwei/
   ├── 易经/六爻   yijing/ + traditional_complete/
   ├── 统一信号    signals/
   ├── 六象合参    inference/
   ├── 宿世节点    past_life/ + topics/
   ├── 中阴链      bardo/ + topics/
   ├── 缘契        relationship/ + topics/
   └── 命势长图    life_chart/
   ↓
PostgreSQL / RLS / Replay / Audit  infra/migrations + apps/api/app/repositories.py
   ↓
DeepSeek 可选成文层  apps/api/app/deepseek_provider.py + prompts
```

核心公开契约是
[`packages/sanji-engine/src/sanji_engine/public.py`](../../packages/sanji-engine/src/sanji_engine/public.py)，
只允许 `validate_request`、`execute`、`replay`、`inspect_ruleset`。规则注册位于
[`rulesets/registry.json`](../../packages/sanji-engine/src/sanji_engine/rulesets/registry.json)，
Schema 位于 [`schemas/`](../../packages/sanji-engine/src/sanji_engine/schemas/)。

Web 只负责输入、状态与渐进披露；FastAPI 负责鉴权、编排和持久化；数据库通过 RLS
实施主体隔离；DeepSeek 不进入核心依赖、Trace 或锁定 Hash。
