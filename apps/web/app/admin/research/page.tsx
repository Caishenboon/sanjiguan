import { EvidenceCard, ResearchWarning, SanjiHeader, SanjiShell } from "@sanji/ui";

export default function ResearchHome() {
  return <SanjiShell><SanjiHeader/><main className="sanji-main">
    <section className="sanji-hero"><div><p className="sanji-kicker">Owner only</p><h1 className="sanji-title">研究中枢</h1><p className="sanji-lede">比较方法，不把差异藏进默认值；查看证据，不让外部项目替代三际枢。</p></div><ResearchWarning>所有展示均为研究预览。未确认传统方法保持 UNCONFIRMED。</ResearchWarning></section>
    <section className="sanji-grid">
      <EvidenceCard title="易经 · 实物三钱"><p>4096 个输入状态，确定性机械变卦。</p><a href="/admin/research/three-coin">打开</a></EvidenceCard>
      <EvidenceCard title="八字 · 多 Profile"><p>74 个边界例与 420 项机械验证。</p><a href="/admin/research/bazi-methods">打开</a></EvidenceCard>
      <EvidenceCard title="紫微 · 三合基础"><p>十二宫、十四主星、Trace 与 Replay。</p><a href="/admin/research/ziwei">打开</a></EvidenceCard>
      <EvidenceCard title="传统机械上游"><p>固定版本八字、紫微、六爻结构与证据图。</p><a href="/admin/research/upstream-traditional">打开</a></EvidenceCard>
      <EvidenceCard title="Oracle 差分"><p>外部参考只提供差分证据，不改变结果。</p><a href="/admin/research/oracles">打开</a></EvidenceCard>
    </section>
  </main></SanjiShell>;
}
