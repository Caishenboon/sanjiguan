import AppShell from "../../../../components/AppShell";import {sixImages,stages} from "../../../../lib/sprint3-fixture";
export default function Analysis(){return <AppShell title="六象合参"><section className="six-grid">{sixImages.map(([n,v,count,counter])=><article className="panel image-card" key={n}><span className="image-glyph">{n[0]}</span><h2>{n}</h2><b>{count} 条证据</b><p>高可靠度 {Math.max(2,count-5)} · 逆证 {counter}</p><small>完整度 {v}% · 已归一</small></article>)}</section>
 <section className="panel"><div className="section-title"><div><p className="eyebrow">实际流水线</p><h2>十五阶段</h2></div><span>六象已合，主次既分，断章成卷。</span></div>
 <ol className="stages">{stages.map((s,i)=><li key={s}><b>{String(i+1).padStart(2,"0")}</b><span>{s}</span><i>完成</i></li>)}</ol></section></AppShell>}
