# 三际观产品主干与用户旅程 v1

## 目标与边界

普通用户按“建立主体 → 记录资料 → 选择工具 → 阅读结果 → 保存与回看”的顺序使用产品。研究管理员保留六象研究、数据源、Signal、Mapping、Trace 与质量报告，但入口只在具有授权角色的“我的 → 研究与管理”中显示。

本轮没有修改 `sanji-engine`、规则集、评分、Golden Hash、数据库迁移或 API 契约，也没有启用易经、八字、紫微到六象的真实 Mapping。

## 信息架构

| 一级入口 | 品牌副标题 | 普通用户任务 |
|---|---|---|
| 首页 | 观三际 | 看见当前可做、最近状态和未完成任务 |
| 记录 | 录一念 | 选择记录类型并保存事实 |
| 合参 | 察诸象 | 按任务选择机械工具或查看研究准备度 |
| 三际录 | 阅往迹 | 筛选、阅读与按原版本回放历史 |
| 我的 | 主体与设置 | 管理主体、隐私、撤回和授权入口 |

主导航固定为五项。普通页面首屏不显示 Engine、Ruleset、Hash、Signal 或数据集 Revision；这些字段只在结果页“研究详情”中渐进披露。

## 路由与权限

| 路由 | 受众 | 用途 | 权限 |
|---|---|---|---|
| `/` | 普通用户 | 首页 | 安全会话 |
| `/onboarding` | 普通用户 | 建立或完善主体 | member / owner |
| `/records` | 普通用户 | 记录中心 | member / owner |
| `/records/new` | 普通用户 | 记录表单 | member / owner |
| `/consult` | 普通用户 | 合参中心 | member / owner |
| `/consult/yijing` | 普通用户 | 实物三钱录入 | member / owner |
| `/consult/bazi` | 普通用户 | 八字机械范围与资料准备 | member / owner |
| `/consult/ziwei` | 普通用户 | 紫微机械范围与资料准备 | member / owner |
| `/consult/liuxiang` | 普通用户 | 六象资料准备度 | member / owner |
| `/results/[id]` | 普通用户 | 白话结果与折叠研究详情 | 资源 owner / viewer |
| `/chronicle` | 普通用户 | 三际录列表 | member / owner |
| `/chronicle/[id]` | 普通用户 | 三际录详情 | 资源 owner / viewer |
| `/me` | 普通用户 | 主体、隐私和设置 | 安全会话 |
| `/admin/**` | 研究管理员 | 既有研究平台 | owner / research_admin |
| `/forbidden` | 普通用户 | 权限不足说明 | 公开状态页 |

`/profile/[id]`、`journal`、`analysis`、`versions`、`more`、`onboarding` 与 `report` 等旧链接保留兼容重定向。尚未开放的宿世、中阴与人生 K 线旧页重定向到“我的”，不会继续展示合成研究结果。

## 标准旅程

1. 首次使用：进入首页 → 建立主体 → 如实填写基本资料 → 保存 → 首页显示下一步。
2. 记录一念：记录中心 → 选择类型 → 填写并保存 → 三际录 → 查看刚保存的记录。
3. 已有工具：合参 → 易经三钱 → 录入六次实物结果 → 阅读机械结果 → 展开研究详情 → 三际录。
4. 六象未成断：六象 → 查看资料准备度 → 得知真实 Mapping 未启用 → 理解暂不成断 → 继续记录资料。

旅程 A、B、C 会在桌面、平板与移动项目上运行。测试中的人物、问题和记录完全虚构；API 使用网络拦截返回固定机械 Fixture，仅验证产品旅程，不作为现实验证或六象证据。

## 数据与会话

- 表单调用既有 FastAPI 主体、日记与实物三钱 API。
- `Idempotency-Key` 由客户端为每次变更请求生成；服务端保持 24 小时语义。
- 浏览器 `sessionStorage` 只暂存当前导航所需的主体、记录与执行摘要，不复制敏感正文，也不作为服务端真值。
- 草稿只保留于当前浏览器会话，并向用户明确说明。
- 未知出生时刻传输为 `local_time = null`、`time_precision = unknown`，不得补造。

## 状态与无障碍

核心页面具有空、加载、保存中、成功、资料不足、网络失败重试、权限不足、撤销、无法回放和研究未启用状态。错误靠近字段并使用 `role=alert`；保存状态使用 `aria-live`。表单均有可关联 Label，主导航有 `aria-current`，状态同时使用文字和形状，不只依赖颜色。移动端主流程单列，研究详情默认折叠，触控目标最小高度 44px。

## 产品词典

唯一来源为 `apps/web/lib/product-language.ts`。其中固定：

- `strength`：象势强度；
- `confidence`：证据可信度；
- `decisive`：象意较明；
- `provisional`：初见其象；
- `contested`：诸象相争；
- `insufficient`：资料不足，暂不成断；
- `counterevidence`：逆证；
- `missingness`：尚缺资料；
- `boundary_sensitivity`：边界敏感；
- `profile dispute`：规则方案存在分歧；
- `replay`：按原版本重放；
- `reanalyze`：用当前版本重新分析。

## 明确未实现

未实现新的六象证据评分、真实 Mapping、宿世、中阴、最终缘契、人生 K 线、最终吉凶、应期或 DeepSeek 正式结论。八字与紫微普通入口目前只完成资料准备与边界说明；将真实机械执行接入普通安全会话仍是后续工作。
