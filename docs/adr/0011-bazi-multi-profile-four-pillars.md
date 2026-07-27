# ADR-0011：八字多 Profile 基础四柱机械引擎

- 状态：Accepted for research
- 日期：2026-07-27
- 适用范围：`sanji-engine` 1.0 研究执行

## 决定

在 `sanji-engine` 内提供三个显式、版本化、并存的研究 Profile。调用方必须传入
`profile_id` 与 `profile_version`，不存在默认 Profile。三者均为
`research_active + UNCONFIRMED + production_activatable=false`。

基础四柱仅包含历史法定时间、太阳时校正、立春年界、十二节月界、版本化日序、
十二时辰和候选敏感性。解释、评分、吉凶、应期及全部后续命理模块不在本决定内。

现有 0.1.0 候选档案继续保留为方法冻结证据；可执行的 1.0.0 Profile 使用独立注册
资产，避免静默改写历史候选档案。

## 理由

这使方法分歧成为输入契约而不是隐藏代码分支，也让相同输入、Profile、规则和数据
版本在 Windows/Linux 上得到相同 Canonical JSON 哈希。研究可执行状态只表示机械
规则可回放，不表示传统正确性、产品认可或生产批准。

## 后果

- 历史法定时间及 IANA/DST 继续复用 Calendar，不得在 API 或页面复制。
- 日序锚点独立版本化；当前仍待合格方法审校。
- `DUAL_SPLIT_ZI` 返回并列轨道，不指定主盘。
- 未知时间枚举最多 26 个候选，不依据人生事件反推唯一时辰。
- D-002、D-003 未冻结，生产门禁继续关闭。
