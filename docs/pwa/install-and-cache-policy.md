# PWA 安装与缓存策略

断点：mobile `<768px`；tablet `768–1199px`；desktop `1200–1599px`；wide `≥1600px`。
在 HTTPS 或 localhost 下，浏览器可从地址栏安装三际观；PC 与手机均使用
`display=standalone` 和 `/profile/demo` 起始页。

Service Worker 仅缓存图标与 manifest。API、档案、出生资料、Evidence、Journal、
Relationship、断章、Token、Session、Prompt 和模型响应均不得缓存。网络失败时手机速记
只保留当前页面内存草稿，不建立长期离线敏感数据库。

各核心页必须保留可见焦点、键盘顺序、非颜色状态提示和 `prefers-reduced-motion`；星图与
曲线提供列表/表格替代。在 390×844、768×1024、1440×900、1920×1080 和 200% 缩放下
执行视觉回归。
