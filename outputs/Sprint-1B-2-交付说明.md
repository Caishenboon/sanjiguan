# Sprint 1B-2 交付说明

本阶段建立三际枢知识谱系与规则工坊：来源登记、知识分层、传统标签、访问与许可、
文献与 Claim、精确 Locator、支持/冲突关系、审核资格、版本、研究规则、影响分析及
研究原型。后台只允许 owner 访问。

所有规则保持非 active 且 `production_activatable=false`。没有接入 DeepSeek、
Embedding、向量检索、RAG、全文抓取、名人匹配或真实用户报告。

关键边界：

- `sealed` 只留最低书目信息，不保存正文、摘要化修法或操作步骤。
- `practice_restricted`、`copyright_restricted`、`unknown` 默认拒绝 RAG 和规则用途。
- system interpretation 不得标作 traditional statement。
- verified Claim 必须有 Locator。
- reviewed 规则必须包含逆证和缺失数据行为。
- 普通生计原型占首批研究原型 25%。

验收包括空库 migrations、重复 migration、漂移检测、PostgreSQL 16 owner-only RLS、
知识/规则静态门禁、Schema/OpenAPI、Web production build 和 Secret Scan。
