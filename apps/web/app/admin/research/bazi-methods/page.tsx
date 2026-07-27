import { BaziFourPillars, ProfileBadge, ResearchWarning, SanjiHeader, SanjiShell, TraceStep } from "@sanji/ui";

const profiles=[
 ["BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1","法定时间／民用午夜候选"],
 ["BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1","地方视太阳时／子初候选"],
 ["BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1","双轨敏感性／早晚子时候选"],
];
const categories=[
 ["时间与时区",8],["年界",4],["月界",38],["日界",7],["时界与未知时间",17],
];

export default function Page(){
 return <SanjiShell><SanjiHeader/><main className="sanji-main">
  <section className="sanji-hero"><div><p className="sanji-kicker">Owner research · BaZi</p><h1 className="sanji-title">四柱边界台</h1><p className="sanji-lede">显式选择 Profile，观察时间校正与边界候选。不含十神、旺衰、格局、吉凶或解释。</p></div><BaziFourPillars/></section>
  <ResearchWarning>D-002、D-003 未冻结；候选机械结果不指定唯一正确主盘。</ResearchWarning>
  <section className="sanji-grid" style={{marginTop:"1rem"}}>
   <article className="sanji-card sanji-card--wide"><h2>Method Profiles</h2>{profiles.map(([id,label])=><p key={id}><ProfileBadge>{id}</ProfileBadge> {label}</p>)}</article>
   <article className="sanji-card"><h2>74 个合成边界例</h2>{categories.map(([name,count])=><p key={name}>{name} · {count}</p>)}</article>
   <article className="sanji-card sanji-card--full"><TraceStep index={1} title="原始法定时间">保留用户输入</TraceStep><TraceStep index={2} title="时间候选">民用、平太阳、视太阳并列</TraceStep><TraceStep index={3} title="四柱候选">Profile 决定边界方法</TraceStep></article>
  </section>
 </main></SanjiShell>
}
