import {
  EvidenceCard, HashPanel, ResearchWarning, RulesetBadge,
  SanjiHeader, SanjiShell, TraceStep, VerdictStatusBadge,
} from "@sanji/ui";
import { evidenceChain, liuxiangDimensions } from "../../../../lib/liuxiang-research-demo";

export default function LiuxiangResearchPage() {
  return <SanjiShell><SanjiHeader/><main className="sanji-main">
    <section className="sanji-hero">
      <div><p className="sanji-kicker">Deterministic research v1</p>
        <h1 className="sanji-title">确定性六象研究</h1>
        <p className="sanji-lede">三际观原创研究体系。结构可回放，结论未审校，不能生产激活。</p>
      </div>
      <ResearchWarning>research_active · UNCONFIRMED · production_activatable=false</ResearchWarning>
    </section>
    <section className="sanji-grid">
      <EvidenceCard title="研究状态"><VerdictStatusBadge status="provisional"/>
        <p>Strength 92.00% · Confidence 78.00%</p><RulesetBadge>liuxiang-inference/1.0.0</RulesetBadge>
      </EvidenceCard>
      <EvidenceCard title="信息完整度"><p>演示资料 86.00% · 独立来源 3</p>
        <p>Profile 分歧与边界敏感度分别计入 Confidence，不混入 Strength。</p>
      </EvidenceCard>
      <EvidenceCard title="确定性证据"><HashPanel label="合成案例聚合 Hash" value="sha256:1620423af9d7411b6329e971e5196c599cdd8914f9a3c6e8277ac4b1015f0944"/></EvidenceCard>
    </section>
    <section className="sanji-grid" style={{marginTop:"1rem"}}>
      {liuxiangDimensions.map(item=><EvidenceCard title={`${item.name} · ${item.id}`} key={item.id}>
        <p><b>Strength</b> {(item.strength/100).toFixed(2)}%　<b>Confidence</b> {(item.confidence/100).toFixed(2)}%</p>
        <p>独立证据 {item.independent} · 逆证 {item.counter}</p>
      </EvidenceCard>)}
    </section>
    <section className="sanji-card sanji-card--wide" style={{marginTop:"1rem"}}>
      <h2>证据链（文本可访问视图）</h2>
      {evidenceChain.map(([title,detail],index)=><TraceStep index={index+1} title={title} key={title}><p>{detail}</p></TraceStep>)}
    </section>
  </main></SanjiShell>;
}
