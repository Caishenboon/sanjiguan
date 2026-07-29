# 公共研究数据、许可证与关联政策

## 数据源

机器可读 Manifest 位于 `research-data/manifests/`。所有下载 URL 固定
Revision，完成后校验 SHA-256。普通 CI 不访问网络，原始大文件不进 Git、
普通 Artifact 或生产镜像。

| 数据源 | 固定 Revision | 许可证结论 | 接入 |
|---|---|---|---|
| [VedAstro 出生资料](https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Birth-Date-Location) | `c8645485d498011d77c6c762127852ccbad4a7d0` | HF 元数据声明 MIT，但固定仓库无独立 LICENSE；仅条件允许本地研究 | enabled |
| [VedAstro 婚恋资料](https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Marriage-Divorce-Info) | `2c297bc38ce348cc7c87d1283bce30a3aaa7583b` | 同上；原始再分发禁用 | enabled |
| [DReAMy-lib DreamBank](https://huggingface.co/datasets/DReAMy-lib/DreamBank-dreams-en) | `d400ee8cd114eaa09b1dbf3e44c2f248b2b1b5ec` | 再包装元数据虽写 Apache-2.0，但无独立 LICENSE 证明原始 DreamBank 正文的授权链 | disabled |

DreamBank 只保留书目与字段信息。正文未下载、未提交、未嵌入，也不得发送
外部 LLM。必须取得原始来源和再发布授权审查结论后，方可另行启用。

## 精度政策

出生时间仅分为 `exact_time`、`approximate_time`、`date_only`、
`year_only`、`unknown`。`date_only` 不补中午或午夜。事件日期仅分为
`exact_date`、`month_only`、`year_only`、`unknown`；年份不补 1 月 1 日。

VedAstro 出生集 15,807 行均含钟表时刻和数值 UTC offset，但没有 IANA
时区与显式 DST 来源。因此“按时刻精度可排”不等于“历史法定时间已核验”。
提供方 `AA` 也不是三际观独立核验。

## 人物关联

顺序严格为：

1. 稳定 source person ID；
2. 精确规范化标识；
3. 姓名+出生年精确匹配；
4. 人工审查队列。

不按模糊姓名自动合并，不用 LLM 猜身份。每个关联记录方法、整数置信度、
冲突字段、人工审查标记与 Provenance。两个 VedAstro 数据集统一使用
`shared_source_group=vedastro_org`，不得称为两个独立验证来源。

## 一键命令

```text
python scripts/research_data.py list
python scripts/research_data.py sync <dataset-id>
python scripts/research_data.py validate
python scripts/research_data.py normalize
python scripts/research_data.py report
python scripts/research_data.py fixture
python scripts/research_data.py clear-cache
```

缓存通过 `SANJI_RESEARCH_DATA_CACHE` 配置，默认位于用户缓存目录。下载使用
`.part` 文件、有限重试与 SHA-256 校验；失败的部分文件不会冒充完整数据。

## 研究解释边界

外部数据不训练运行时模型，不自动调权重。允许输出覆盖、样本数、效应方向、
不确定区间、基率与分层置换比较。回顾性相关不等于预测力；查看测试结果后
修改规则的实验不得继续称为盲测。规则候选必须人工审核，默认
`draft/disabled`。
