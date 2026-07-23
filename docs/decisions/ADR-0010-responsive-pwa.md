# ADR-0010：PC 优先的响应式 PWA

状态：accepted

三际观采用 PC 优先的响应式 PWA。PC/平板承载深度研究，手机承载梦境、事件和观照记录：
“大屏观三际，小屏录一念”。当前不开发原生应用，未来共用 Next.js、FastAPI 和 PostgreSQL。

本 Sprint 不实现 Service Worker 敏感数据缓存。出生、关系、日志、报告、Token 和 API
敏感响应不得离线缓存。
