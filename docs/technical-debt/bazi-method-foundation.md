# 八字方法基座技术债

1. D-002 仍缺合格八字方法审校人、可定位来源组合及 23:00–01:00 签字样例。
2. 年/月柱使用立春与十二节的传统来源谱系仍需独立整理；天文来源不能代替。
3. D-003 旺衰、起运、顺逆不在本 Sprint；已有公版文字只作为发现线索。
4. IANA 早期历史与地点行政边界需逐地点交叉核验。
5. 格里历改革前的输入语义和生产支持窗口未冻结。
6. `source_attested` 四柱金样例为 0；不得把 profile-discriminating 案例升级冒充。
7. 当前 Owner 工作台复用 Claim 工坊记录意见，尚无专门 Method Profile 审批状态机。
8. 未来 Profile 冻结必须提升版本，不得修改现有候选资产并静默重算历史结果。
9. 两个既有 PostgreSQL 集成测试使用固定 fixture 键（`knowledge_topics.slug=allowed`、`evaluation_cases.id=owner-case`）且不自行清理；同一测试库重复运行前需精确清理。CI 每次使用空库，当前远程语义不受影响，但后续应使测试具备自清理能力。
