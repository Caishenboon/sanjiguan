# sanji-engine

`sanji-engine` 是三际观 Monorepo 内可独立安装的确定性核心。它不依赖 Web、API、数据库、
网络或 LLM。公开入口仅位于 `sanji_engine.public`：

```python
validate_request
execute
replay
inspect_ruleset
```

当前 Calendar 基础组件、Signals/Inference 研究基线以及实物三钱机械起卦可执行。
实物三钱仅生成本卦、动爻与变卦，不含解释、吉凶或应期。八字、紫微、解释性易经、中阴、宿世身份、因缘评分和人生
K 线均返回结构化 `MODULE_DISABLED`，没有临时算法。

本包和其规则、知识、测试数据的许可证仍未确定；不得公开发布。
