# 核心边界与迁移地基 Sprint 交付说明

## 已交付

- 独立可安装的 Python 3.11+ `sanji-engine` 包及 Engine API 1.0。
- JCS 兼容 Canonical JSON 子集、内容哈希、Trace 与 Replay Manifest。
- Calendar 等价迁移和原应用兼容适配；原时间、时区、太阳时及节气测试保持通过。
- 所有未确认术数模块结构化禁用；无占位计算。
- Signals/Inference 研究行为冻结元数据，明确非权威金样例。
- analysis_runs manifest 字段迁移草案；不回填历史数据。
- Linux/Windows 固定哈希验证、独立边界与依赖静态门禁。

## 未实现且继续阻断

八字、紫微、易经、中阴、宿世身份、因缘评分、人生 K 线、生产
Signals/Inference、DeepSeek 核心接入及真实历史回放迁移均未实现/未激活。

## Calendar 差异记录

本次迁移未主动修正旧行为。兼容测试逐字段覆盖历史时区、DST、未知时间、
地方平/视太阳时、日期/时辰边界和节气瞬时；若后续发现问题，须新增差异记录
与规则版本，不得在现有版本中静默变更。

## 验收

运行 `python -m unittest tests.test_sanji_engine_core tests.test_sprint1a_time -v`
及 `python scripts/validate_sanji_engine.py`。CI 的 `sanji-engine-determinism`
在 Windows 与 Linux 对同一案例核对固定 output hash。
