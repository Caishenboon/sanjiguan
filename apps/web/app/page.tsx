import { EvidenceCard, ResearchWarning, SanjiHeader, SanjiShell } from "@sanji/ui";

export default function HomePage() {
  return (
    <SanjiShell><SanjiHeader/><main className="sanji-main">
      <section className="sanji-hero"><div><p className="sanji-kicker">过去 · 当下 · 未来</p><h1 className="sanji-title">三际观</h1><p className="sanji-lede">观因于往际，察缘于当下，见势于未来。以可追溯证据承载研究，不让模型替代确定性计算。</p></div><ResearchWarning>当前仅开放工程基础与 Owner 研究工具；未审校规则不会产生生产术数结论。</ResearchWarning></section>
      <nav aria-label="主要入口" className="sanji-grid">
        <EvidenceCard title="三际录"><p>保存原始记录、来源、确认状态与撤回边界。</p><a className="sanji-btn" href="/profile/demo">开始观命</a></EvidenceCard>
        <EvidenceCard title="机械研究"><p>显式 Profile、完整 Trace、版本与哈希始终可见。</p><a className="sanji-btn" href="/admin/research">续观三际录</a></EvidenceCard>
        <EvidenceCard title="安全边界"><p>邀请制、资源级授权、密钥只在服务端环境变量。</p><a className="sanji-btn" href="/about">了解边界</a></EvidenceCard>
      </nav>
    </main></SanjiShell>
  );
}
