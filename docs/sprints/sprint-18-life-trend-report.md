# Sprint 18 交付说明：命势长图、人生 K 线与三际断章

## 已交付

- `sanji-engine/life-chart` 独立确定性执行；
- Life Trend Ruleset、整数 OHLC、空白桶、未来可信度递减；
- 吉凶状态机、应期窗口、18 段断章和无 AI 成文；
- DeepSeek 最小输入、Schema/事实/认识状态校验和失败回退；
- 核心、模板、叙事输入与叙事输出 Hash 分离；
- PostgreSQL 迁移、FORCE RLS、加密快照、三际录；
- Replay、Reanalysis 与版本差异比较；
- 薄 API、桌面/移动共用页面、图形与文字表格双重阅读；
- 48 个 `synthetic_conformance` 案例和跨平台聚合 Hash；
- 受控成文攻击测试、OpenAPI、JSON Schema 和静态门禁。

## 研究限制

规则保持 `sanji_original / research_active / UNCONFIRMED /
production_activatable=false`。没有启用未经审校的八字、紫微、易经解释性 Mapping；
没有训练权重、现实准确率声明、精确无条件未来预测或生产激活。

## 未做

没有进行全站 UX 重构、生产部署、备份换机、开源发布、支付会员、新公共数据集、
第二套 AI 平台、微服务或下一 Sprint 工作。

## 验证入口

```text
python -m unittest tests.test_sanji_engine_life_trend_v1 -v
python scripts/validate_life_trend_v1.py
python scripts/export_life_trend_openapi.py --check
pnpm --dir apps/web build
```
