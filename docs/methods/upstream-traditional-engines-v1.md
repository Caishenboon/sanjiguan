# 传统算法上游集成 V1

状态：`research_active / UNCONFIRMED / production_activatable=false`。

本集成只承认固定版本开源实现实际提供的机械结构，不将“代码存在”写成传统共识。锁文件为
`third_party/upstream-lock.json`，核心规则集为 `sanji-upstream-composite-1.0.0`。

## 边界

- 八字：`lunar-python 1.4.8` 提供四柱、藏干、十神、五行字段和纳音等机械字段。未准入旺衰、格局、用神或人生解释；公开候选 `richard3153/bazi-calculator` 无法完成源码与许可证复核，已拒绝。
- 紫微：`iztro 2.5.8` 通过本地 Node 进程提供命宫、身宫、五行局、十二宫和主星结构；现代解释文本不进入输出。闰月与四化流派差异保留为争议。
- 六爻：`liuyao-engine 0.1.0` 的 `hexagram.py` 精确快照提供卦宫、纳甲、六亲、六神、世应与变卦结构。上游完整包依赖 `sxtwl`，Windows 缺少可安装轮子，因此仅 vendor 无需该依赖的原文件，保留 Apache-2.0 LICENSE/NOTICE 且不修改源码。用神、旺衰、最终吉凶与应期不在本次准入范围。
- `najia 2.0.1` 只作差分对照，不参与运行时多数投票。

## 确定性与证据图

所有适配器拒绝隐式 Profile。八字当前只接受 `lunar-python-sect1@1.0.0`，并显式冻结 `sect=1` 与“使用调用方已规范化的地方墙上时间”；太阳时、时区和日界选择仍由既有上游边界之前的时间链处理。紫微只接受 `iztro-lunar-standard@2.5.8`，并显式记录 `iztro_fix_leap_true` 闰月政策。六爻只接受 `yaomancy-liuyao-engine-0.1.0@1.0.0`，六爻顺序固定自下而上。

每个适配器输出固定的上游名称、版本、提交、许可证、Profile、规范化输入、警告、争议、Trace、原始 Hash 与 Canonical Hash。核心不导入上游包，只验证适配器锁定身份并构建 Canonical Evidence Graph。

同一上游与同一原始 Hash 只形成一个独立证据组；争议不被平均或抹除。由于没有审校通过的解释映射，组合结果固定返回 `strength_bp=0`、`confidence_bp=0` 与 `insufficient`，避免机械字段被伪装为命断。

Replay 使用已保存的规范化适配器结果，不依赖未来的可变上游安装。Reanalysis 创建新记录；旧版本、旧 Hash 与旧 Ruleset 不会被覆盖。

## 数据与隐私

适配器离线运行，不访问网络、不调用 LLM。API 仅供 owner 研究区使用，输入与结果在 PostgreSQL 中加密，RLS 强制隔离。日志不记录完整出生资料或卦盘输入。

## 验证资产

- 八字适配器：60 个合成机械案例。
- 紫微适配器：48 个合成机械案例。
- 六爻适配器：全部 4096 组 6/7/8/9 状态。
- 六爻独立差分：64 个静态本卦逐项比对 `najia 2.0.1` 的卦名、卦宫、世应与六亲。
- 组合：输入顺序不变性、锁校验、零解释评分、Evidence Graph、Replay。

固定 Hash 见 `tests/fixtures/upstream-traditional-hashes-v1.json`。这些是工程一致性资产，不是现实准确性证明或权威传统金样例。
