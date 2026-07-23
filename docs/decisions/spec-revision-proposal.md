# 规格冲突与缺口修订提案

## R-001：Sprint 0“冻结方法”与待负责人确认冲突

将 Sprint 0 验收改为：“工程门禁、方法候选与证据包建立完成；D-001 至 D-007 经负责人签署后才算方法冻结。”方法未冻结时允许进入不依赖术数结果的 Sprint 1 工作，但不得实现生产算法。

## R-002：MVP 紫微范围

把“MVP 必须完成紫微”改为：“MVP 完成经过验证的基础排盘与重点宫位结构摘要；高级飞化、流月/流日/流时、完整格局和宿世映射延期至 V1.1。”基础字段见方法选型包。

## R-003：UUIDv7

明确 UUIDv7 由应用层库生成；数据库仅校验 UUID 类型。选定运行时库后增加排序性/时钟回拨测试，不依赖 PostgreSQL 16 未统一提供的生成函数。

## R-004：Idempotency-Key

新增 `idempotency_records(scope_owner_id, method, route_template, key_hash, request_fingerprint, state, status_code, response_encrypted, resource_id, created_at, expires_at)`。

- 写操作必须带 key；key 作用域为用户 + HTTP 方法 + 路由模板。
- 指纹为 canonical body + 影响语义的查询参数，不含 Authorization/Cookie。
- 首次请求创建 `processing`；同 key 同指纹完成后重放原状态码/响应；处理中返回 409；同 key 异指纹返回 422；缺失返回 400。
- 普通写操作保留 24 小时；分析/报告/导出等有外部成本的操作保留 30 日。
- 参数校验失败和进入业务执行前的冲突不缓存；业务执行开始后的确定响应缓存。
- DELETE 仍支持 key，因为删除编排并非单一数据库删除。

依据：[IETF Idempotency-Key draft](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header)、[Stripe 实践](https://docs.stripe.com/api/idempotent_requests)。

## R-005：RLS、owner 与 viewer

新增 `profile_grants(id, profile_id, grantee_user_id, permission, granted_by, created_at, expires_at, revoked_at)`；viewer 只能拥有 `read`，默认过期且可撤销。

- RLS 使用当前主体 ID + 未撤销 grant；owner 管理操作通过独立受审计服务角色，不复用应用连接。
- 所有用户表 `FORCE ROW LEVEL SECURITY`；应用角色不得为表 owner、superuser 或 `BYPASSRLS`。
- profile、evidence、charts、runs、reports、relationships、journal、versions 都做直接或安全函数关联策略。
- 每个策略有 owner/viewer/撤销/过期/跨租户测试；外键唯一约束可能构成旁道，错误统一返回 404。

## R-006：关系对象同意

将单一加密字段升级为 `relationship_consents`：subject_id、consent_version、scope、evidence_kind、consented_at、expires_at、revoked_at、record_encrypted、record_hash、created_by。分析前必须存在有效同意，或 subject 为 `anonymous_event` 且无可识别字段。撤回后阻断新分析并启动既有派生数据删除/匿名化流程。

## R-007：删除与不可变备份

把“立即硬删除”拆成：

1. 立即逻辑不可访问与会话/分享撤销；
2. 24 小时内删除活动主库、缓存、向量、对象和队列；
3. 删除该用户 envelope key，完成加密擦除；
4. 备份随最长期限（建议 ≤30 日）自然过期，恢复流程带 deletion tombstone，禁止恢复已删用户；
5. 手工快照必须登记、限期并由删除编排枚举。

报告向用户展示活动系统完成时间和备份最晚消除日期，不宣称瞬时物理擦除。

## R-008：K 线规范

先定义五条原始子线 `z_i(t)` 为各自规则信号经可靠度、持续期和数据质量加权后的 `[-1,1]` 值。综合原始值：

`r(t)=0.24*w+0.22*p+0.20*v+0.18*rel-0.16*k`。

明确这不是普通权重均值；将理论范围 `[-0.16, 0.84]` 线性映射为：

`index(t)=clip(100*(r(t)+0.16), 0, 100)`。

若产品改用其他中心/尺度，必须新建公式版本，不能静默改。OHLC 草案：

- `open_t = close_{t-1}`；首窗取窗口首点。
- `high_t = max(smoothed_path within window)`。
- `low_t = min(smoothed_path within window)`。
- `close_t = window end point`。
- 强制 `low ≤ open,close ≤ high`，只作数值不变量，不通过事后修饰“美化”走势。

置信带对不确定输入候选和允许的参数 bootstrap/枚举分布取预注册分位数（建议 P10/P90）；样本不足时不报精确带，只报数据质量等级。三轨只修改白名单行为矩阵，不回写传统排盘。

此公式仍是**工程提案，不是传统原义**，须产品确认后才实现。

## R-009：规则来源不足的发布门槛

规则激活必须同时满足：A/B 级来源或指定专家签署；claim layer；精确 locator；许可状态；method_id/version/checksum；正例/反例/模糊例；单测与回放；双人审批。只有 C 级来源、无定位页码、无许可或专家分歧未解决的规则只能保持 draft。X 级来源不可入库。

## R-010：模型与向量维度

模型名、token 价格、并发和向量维度都属于运行配置。embedding 表记录 `model_id` 和 `dimensions`，staging 使用不定维 `vector`；选定模型后以局部表达式索引固定维度。切换模型必须新建 embedding 版本并重建索引，禁止在同一索引混合维度。
