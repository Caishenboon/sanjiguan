# 三际观 V1 展示 Token

本轮沿用现有三际观设计系统，不引入第二套 UI 框架或远程字体。

| Token | 用途 |
| --- | --- |
| `--ink` / `--surface-1` | 墨黑主背景与基础表面 |
| `--indigo` / `--surface-2` | 深靛层次表面 |
| `--gold` | 暗金主行动、象名与当前步骤 |
| `--cinnabar` / `--danger` | 朱砂警示、逆证与不可逆操作 |
| `--lotus` | 莲白正文 |
| `--bluegray` / `--text-muted` | 青灰辅助信息 |
| `--positive` | 成功状态；始终同时显示文字/图标 |
| `--warning` | 不成断与资料缺口；始终同时显示原因 |
| `--focus` | 键盘焦点环 |
| `--radius-*` / `--shadow-soft` | 统一圆角与层级阴影 |

章节、象名与标题使用仓库内 Noto Serif SC 及系统宋体回退；正文和表单使用 Noto Sans SC；Hash 与技术字段使用 Noto Sans Mono。禁止未授权远程字体。

用户页面优先复用 `PageState`、`VerdictBanner`、`MetricPair`、`TechnicalDetails`、按钮、步骤条与确认对话框。吉凶、相争、不成断均由文字、边框及图标共同表达，不只依赖颜色。
