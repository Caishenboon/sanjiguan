import { HashPanel, ResearchWarning, RulesetBadge, SanjiHeader, SanjiShell, YijingHexagram } from "@sanji/ui";

export default function Page(){
 return <SanjiShell><SanjiHeader/><main className="sanji-main">
  <section className="sanji-hero"><div><p className="sanji-kicker">Owner research · Yijing</p><h1 className="sanji-title">实物三钱</h1><p className="sanji-lede">逐爻录入真实投掷结果，机械形成卦象。系统不随机投掷、不倒置爻序，也不提供正式断语。</p></div><YijingHexagram/></section>
  <ResearchWarning>traditional_mechanical · research_active · production_activatable=false</ResearchWarning>
  <section className="sanji-grid" style={{marginTop:"1rem"}}><article className="sanji-card sanji-card--wide"><h2>录入约定</h2><p>heads=3、tails=2；六爻自下而上。任何旧记录若缺少映射均不能猜测回填。</p></article><article className="sanji-card"><RulesetBadge>physical-three-coin/0.1.0</RulesetBadge><HashPanel label="示例 Domain hash" value="sha256:synthetic-visual-fixture"/></article></section>
 </main></SanjiShell>
}
