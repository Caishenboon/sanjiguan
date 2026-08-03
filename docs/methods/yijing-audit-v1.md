# 易经三钱机械实现审计 v1

## 当前机械 Profile

`YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1/1.0.0` 接收六次实物三钱结果，顺序自下而上。每枚钱输入值只能为 2 或 3；三枚之和形成 6、7、8、9：

- 6：老阴，阴爻，动后为阳；
- 7：少阳，不动；
- 8：少阴，不动；
- 9：老阳，动后为阴。

初至三爻构成下卦，四至上爻构成上卦；本卦和变卦按 `king-wen-hexagrams-1.0.0.json` 的六十四卦结构、序号和名称解析。代码位于 `packages/sanji-engine/src/sanji_engine/yijing/three_coin.py`。

## 证据与限制

- 六十四卦名称/序号结构可与 Unicode Yijing Hexagram Symbols 名称表和公开传本核对。
- Unicode 标准不证明投币数值约定或断卦法。
- 当前 2/3 币面约定虽被契约固定，但尚无正式出版或原典来源登记，应为 `SCHOOL_SPECIFIC / PROFILE_REQUIRED`。
- 卦辞、爻辞没有进入评分或判断；输出的 interpretation、auspiciousness 和 period 均为空。

## 当前行为样本

- 普通：六次静爻得到本卦，变卦与本卦相同。
- 0 动爻：moving lines 为空。
- 1 动爻：只翻转对应爻。
- 多动爻：完整列出所有动爻并机械生成变卦，不选择解读策略。
- 缺失/非法：不是六次、每次不是三枚、或值不为 2/3 时拒绝。

`tests/test_sanji_engine_yijing.py` 穷举 4096 个线态并验证唯一确定性 Hash、Replay 和跨平台一致性。

## 明确未实现

三钱起卦不等于完整六爻纳甲断卦。以下全部为 `NOT_IMPLEMENTED / DISABLED`：纳甲、世应、六亲、六神、月建、日辰、旬空、用神、旺衰、进退神和完整断卦规则。

V1 Profile 建议只冻结机械录入、爻序、卦变和结构展示；多动爻只展示，不在本轮选择传统解释法。
