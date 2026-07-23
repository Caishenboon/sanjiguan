# Claim 与规则审查工作流

Claim 状态为 `draft → researched → reviewed → approved → retired`，或 `draft → rejected`。
创建者不能单独批准自己创建且拟用于生产的 Claim。传统、传承、版权访问、工程事实与
系统解释分别要求相应资格；系统解释必须由产品负责人批准并显式标记非传统原义。

修改被规则引用的 Claim 时，关联规则立即标记 `needs_review`。无精确 Locator 不得
标记 verified；disputed 只进入研究界面；rejected/retired 默认不进入检索。

规则进入 reviewed 前必须有正向条件、加减分证据、硬冲突、逆证、缺失数据行为、
适用与不适用边界。Sprint 1B-2 的所有规则 `production_activatable=false` 且不能 active。
