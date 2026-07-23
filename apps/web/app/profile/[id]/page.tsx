import Link from "next/link";import AppShell from "../../../components/AppShell";import ResearchLaunch from "../../../components/ResearchLaunch";
import {evidence,sixImages} from "../../../lib/sprint3-fixture";
export default function ProfilePage(){return <AppShell title="三际录" owner><section className="record-head panel">
 <div><p>档案名</p><h2>无名命卷</h2></div><dl><div><dt>卷号</dt><dd>SJ-0003</dd></div><div><dt>建立</dt><dd>2026-07-23</dd></div>
 <div><dt>出生精度</dt><dd>时辰候选</dd></div><div><dt>Ruleset</dt><dd>0.1.0-research</dd></div><div><dt>版本</dt><dd>卷三</dd></div></dl></section>
 <div className="dashboard-grid"><section className="panel span-2"><div className="section-title"><h2>六象完备度</h2><small>仅代表资料完整度，不代表吉凶</small></div>
 <div className="completeness">{sixImages.map(([n,v])=><div key={n}><span>{n}</span><b>{v}%</b><i style={{"--value":`${v}%`} as React.CSSProperties}/></div>)}</div></section>
 <section className="panel verdict-card"><p className="eyebrow">当前断章</p><h2>行旅求法，学成待传</h2><p>主断已锁定 · 强度 82 · decisive</p><div className="tags"><span>利中有戒</span><span>研究成断</span></div><Link href="/profile/demo/report">查看全文 →</Link></section>
 <section className="panel"><h2>最近证契</h2><ul className="event-list">{evidence.map(e=><li key={e[1]}><b>{e[0]}</b><span>{e[1]}</span><small>{e[2]}</small></li>)}</ul></section>
 <section className="panel"><h2>待补资料</h2><ul className="missing"><li><b>梦境早期记录</b><span>影响梦象 · 不阻断</span></li><li><b>出生时刻</b><span>影响命象 · 边界敏感</span></li></ul></section>
 <section className="panel quick-links"><h2>功能入口</h2><Link href="/profile/demo/samsara-map">观宿世星图</Link><Link href="/profile/demo/life-chart">观命势长图</Link><Link href="/profile/demo/relationships">观缘契资料</Link></section></div>
 <ResearchLaunch/></AppShell>}
