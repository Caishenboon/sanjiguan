# Sprint 2 交付说明

已建立 Owner-only、完全虚构/研究档案限定的确定性研究推演闭环：统一信号、候选、
动态评分、逆证和冲突、排序、宿世研究节点、中阴链断点、PostgreSQL 全文检索、
锁定成断、Fake/DeepSeek/模板赋辞与三际断章预览。

DeepSeek Provider 只在服务端读取 `DEEPSEEK_API_KEY`，默认未配置；CI 使用 Fake
Provider。Embedding Provider 默认 disabled，不固定维度。Provider 失败时回退模板，
确定性推演不依赖模型成功。

所有规则继续 `production_activatable=false`。普通 member/viewer 无权调用研究 API；
未开放生产报告入口。
