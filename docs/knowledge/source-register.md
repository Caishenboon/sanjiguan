# 来源登记册（Sprint 1B-2）

本登记册只确定来源、许可与摄入前置条件，不代表已经摄入正文。

| 来源 | 传统/领域 | 初始访问等级 | 可摄入范围 | 核查依据 |
|---|---|---|---|---|
| BDRC BUDA | 藏文佛教、苯教（分开标注） | 逐条判定 | 书目；仅明确开放项目可进一步评估 | [BDRC Access Policies](https://www.bdrc.io/access-policies/) |
| 84000 | 藏传佛教经典翻译 | open_license / citation_only | 元数据可按 CC BY；译文须依具体 CC BY-NC-ND 条款，不得改写冒充原文 | [84000 Terms of Use](https://www.84000.co/documents/terms-of-use) |
| FPMT | 格鲁传承公开教法 | practice_restricted 默认 | 书目与公开许可说明；需灌顶内容不摄入步骤 | [FPMT restricted practice example](https://shop.fpmt.org/edownload.asp?eid1=1103&eid2=FA9EF1B4TLRH8Xy&file=0) |
| USNO AA | astronomy | engineering_fact | 官方数据服务说明与可复核输出 | [USNO API](https://aa.usno.navy.mil/data/api) |
| PostgreSQL 文档 | engineering | engineering_fact | 按官方文档许可和署名要求登记 | https://www.postgresql.org/docs/ |
| OWASP | engineering | engineering_fact | 按具体页面许可登记 | https://owasp.org/ |
| 香港天文台 | astronomy | unknown | 当前只登记书目；许可核验前不摄入正文 | https://www.hko.gov.hk/ |

## 强制规则

- “网页可访问”不等于允许全文使用。
- BDRC 明确区分开放、版权受限和 sealed；sealed 只保存最低书目信息。
- 84000 的译文与元数据许可不同，必须按对象分别记录。
- `unknown`、`practice_restricted`、`sealed` 默认禁止全文、Embedding、RAG、Prompt 和生产规则。
- AI 生成文本不能登记为传统依据。
