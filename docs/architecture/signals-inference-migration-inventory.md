# Signals / Inference 迁移前现状盘点

状态：迁移前冻结；本文件描述 `0.1.0-research` 的既有行为，不认可其理论正确性。

## 真实调用链

1. `apps/api/app/research_routes.py` 保持 Owner-only、研究同意、外部模型逐次同意，
   解密研究输入并调用 `packages.research_inference.engine.run_inference`。
2. 当前输入已经包含统一 Signal；仓库内没有“原始三际录 → Signal”的可运行映射算法。
   30 个完全虚构案例由 `tests/test_research_inference.py` 的 `case_payload` 生成 Signal。
3. `run_inference` 按 `independence_group` 保留贡献绝对量最大的 Signal；相等时保留先出现者。
4. 根据出现的 domain 归一化固定领域权重；`gua` 被显式排除。
5. 候选来自 `knowledge/research/inference-archetypes.json`：先取 tag 命中项，再按资产顺序
   补足五项，并保证 ordinary_livelihood 候选存在。
6. 支持/反对贡献、硬冲突、跨三领域 bonus、grandiosity penalty 及 sigmoid strength
   均由 `knowledge/research/scoring-config.json` 控制。
7. 排序键为 `(-raw_score, id)`；最终保留五项。ordinary 候选替换后再次使用同一排序键。
8. 状态依次判断 completeness、硬冲突、decisive strength/domain/margin、
   contested margin，否则 provisional。
9. 前三候选各生成一个研究节点；节点仅引用候选和证据，不是正式宿世分类。
10. API 将锁定结果持久化；检索、权限、RLS、审计、模板/DeepSeek 成文继续属于应用层。
    DeepSeek 只读取 allowlist 后的锁定字段，不能改变推演结果。

## 迁移边界

| 处理 | 内容 |
|---|---|
| 迁入 sanji-engine | Signal 验证/去重/稳定顺序、候选生成、权重兼容计算、评分、逆证、冲突、排序、状态、研究节点、领域 Trace、领域哈希与 Replay |
| 旧入口改为薄适配器 | `packages/research_inference/engine.py` |
| 保留在应用层 | Owner 权限、同意、PostgreSQL、加密、HTTP、检索持久化、页面、模板和 DeepSeek |
| 删除/停止调用 | 应用层独立评分、排序和状态判定实现；迁移完成后旧模块不再拥有算法副本 |
| 明确不处理 | 原始资料到正式六象 Signal 的映射、正式权重、八字/紫微/易经/宿世/中阴/因缘/K线算法、文学 Prompt |

## 冻结内容

`tests/fixtures/signals-inference-research-baseline.json` 保存 30 个合成输入及完整领域结果。
领域等价投影包含 Signal 顺序、独立组、权重、候选贡献、支持/逆证、硬冲突、分数、
排名、状态、前三研究节点和锁定哈希。

排除项仅为 notice、数据库/持久化生成 ID、运行时间戳、本机路径和 Provider 成文。
这些字段不参与领域等价或稳定哈希。

## 已知技术债

- 既有计算使用 Python 二进制浮点、`round` 和 `math.exp`。本 Sprint 为保持逐值等价
  暂不重校准；未来转换整数基点/Decimal 必须建立新方法版本。
- 去重相等时依赖输入顺序；迁移必须显式保存该既有 tie-break，不得悄悄更改。
- 候选补足依赖 archetype 资产顺序；资产顺序因此属于本研究方法版本的一部分。
- 既有阶段列表含检索、成文和持久化名称，但这些不是 Engine 内部算法步骤；
  迁移后保留兼容展示，同时用机器 Trace 表达真实领域链。
- 当前 hard conflict 只检查输入 Signal tag；未形成独立“软冲突”模型。
- 当前研究节点名为 past_life_nodes，但只属研究预览结构，不是正式宿世算法。
