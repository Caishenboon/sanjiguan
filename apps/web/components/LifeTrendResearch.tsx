"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import ProductShell,{PageState,TechnicalDetails} from "./ProductShell";
import {apiRequest,readProductSession} from "../lib/product-session";
import {productStatus} from "../lib/product-language";

type Candle={open:number;high:number;low:number;close:number};
type Bucket={bucket_id:string;start:string;end:string;segment:string;candle:Candle|null;confidence_bp:number;coverage_bp:number;status:string;auspice:{label:string};missing:string[]};
type Window={window_id:string;start:string;end:string;type:string;confidence_bp:number};
type Report={chapter:string;symbolic_title:string;image_text:string;plain_interpretation:string;past:string;current:string;future:string;auspice:string;action_guidance:string};
type Run={id:string;archive_id:string;status:string;timeline:Bucket[];timing_windows:Window[];report:Report;core_output_hash:string;deterministic_report_hash:string;trace_hash:string};
type Evidence={factor_id:string;factor_type:string;occurred_on:string|null;tags:string[]};
const SEGMENT:Record<string,string>={observed_past:"往际事实",current_state:"当下",projected_future:"未来推演",insufficient_gap:"资料留白"};

function Trend({values}:{values:Bucket[]}){
  const points=values.filter(v=>v.candle);
  if(!points.length)return <PageState kind="insufficient" title="资料不足，暂不生成曲线"><p>空白时间段不会被随机插值或补造。</p></PageState>;
  const x=(i:number)=>24+i*(552/Math.max(1,points.length-1));const y=(n:number)=>120-(n/10000)*92;
  const path=points.map((v,i)=>`${i?"L":"M"} ${x(i)} ${y(v.candle!.close)}`).join(" ");
  return <figure className="trend-figure"><svg viewBox="0 0 600 240" role="img" aria-label="命势时间序列，未来推演使用空心点"><line x1="20" y1="120" x2="580" y2="120" className="trend-zero"/><path d={path} className="trend-line"/>{points.map((v,i)=><g key={v.bucket_id}><line x1={x(i)} x2={x(i)} y1={y(v.candle!.high)} y2={y(v.candle!.low)} className="trend-wick"/><circle cx={x(i)} cy={y(v.candle!.close)} r="5" className={v.segment==="projected_future"?"trend-future":"trend-point"}/></g>)}</svg><figcaption>有证据的窗口才形成势位；未来为空心点。空白窗口不连线补值。</figcaption></figure>
}

export default function LifeTrendResearch(){
  const[profile,setProfile]=useState("");const[evidence,setEvidence]=useState<Evidence[]>([]);const[run,setRun]=useState<Run>();const[granularity,setGranularity]=useState("auto");const[state,setState]=useState("loading");const[error,setError]=useState("");
  useEffect(()=>{const id=readProductSession().subject?.id||"";setProfile(id);if(!id){setState("ready");return}apiRequest<{factors:Evidence[]}>(`/api/v1/profiles/${id}/life-trend/evidence`).then(v=>{setEvidence(v.factors);setState("ready")}).catch(e=>{setError(e instanceof Error?e.message:"读取失败");setState("error")})},[]);
  async function start(){setState("running");try{setRun(await apiRequest<Run>(`/api/v1/profiles/${profile}/life-trend/executions`,{method:"POST",body:JSON.stringify({granularity,future_bucket_count:2,title:"命势长图与三际断章"})}));setState("ready")}catch(e){setError(e instanceof Error?e.message:"执行失败");setState("error")}}
  if(state==="loading")return <ProductShell title="命势长图" eyebrow="合参 · 三际断章"><PageState kind="loading" title="正在读取授权资料"><p>私人正文不会发送给外部模型。</p></PageState></ProductShell>;
  return <ProductShell title="命势长图" eyebrow="合参 · 三际断章" status="research only"><aside className="privacy-note"><b>三际观原创研究 · UNCONFIRMED</b><p>人生K线不是证券价格，也不是现实准确率声明；往际与未来推演会明确分区。</p></aside>
    {!profile?<PageState kind="insufficient" title="先建立或选择主体"><Link className="product-button" href="/onboarding">建立主体</Link></PageState>:<section className="product-form"><h2>准备本次观察</h2><p>{evidence.length} 项结构事实与授权记录可用；Coverage 只影响可信度，不抬高势位。</p><label><span>时间粒度</span><select value={granularity} onChange={e=>setGranularity(e.target.value)}><option value="auto">按资料精度自动选择</option><option value="month">月</option><option value="quarter">季</option><option value="year">年</option><option value="phase">多年阶段</option></select></label><button className="product-button" disabled={state==="running"} onClick={start}>{state==="running"?"正在确定性计算…":"生成命势长图与断章"}</button></section>}
    {error&&<PageState kind="error" title="本次执行未完成"><p>{error}。已有三际录未被覆盖，可重试。</p></PageState>}
    {run&&<><section className="chronicle-detail"><header><span>{productStatus(run.status)}</span><h2>{run.report.chapter}</h2><p>{run.report.image_text}</p></header><Trend values={run.timeline}/><div className="table-scroll"><table><caption>命势长图文字表格回退</caption><thead><tr><th>窗口</th><th>性质</th><th>开/高/低/收</th><th>可信度</th><th>覆盖</th><th>吉凶</th></tr></thead><tbody>{run.timeline.map(v=><tr key={v.bucket_id}><th>{v.start}—{v.end}</th><td>{SEGMENT[v.segment]}</td><td>{v.candle?`${v.candle.open/100} / ${v.candle.high/100} / ${v.candle.low/100} / ${v.candle.close/100}`:"留白"}</td><td>{v.confidence_bp/100}%</td><td>{v.coverage_bp/100}%</td><td>{v.auspice.label}</td></tr>)}</tbody></table></div><div className="mobile-buckets" aria-label="命势长图移动端文字列表">{run.timeline.map(v=><article key={v.bucket_id}><h3>{v.start}—{v.end}</h3><p>{SEGMENT[v.segment]} · {v.auspice.label}</p><dl><div><dt>开 / 高 / 低 / 收</dt><dd>{v.candle?`${v.candle.open/100} / ${v.candle.high/100} / ${v.candle.low/100} / ${v.candle.close/100}`:"留白"}</dd></div><div><dt>证据可信度 / 覆盖</dt><dd>{v.confidence_bp/100}% / {v.coverage_bp/100}%</dd></div></dl></article>)}</div></section>
      <article className="report-reader"><span>三际断章</span><h2>{run.report.symbolic_title}</h2><p>{run.report.plain_interpretation}</p><h3>往际</h3><p>{run.report.past}</p><h3>当下</h3><p>{run.report.current}</p><h3>未来</h3><p>{run.report.future}</p><h3>吉凶</h3><p>{run.report.auspice}</p><h3>应期</h3>{run.timing_windows.length?run.timing_windows.map(v=><p key={v.window_id}>{v.start}—{v.end} · {v.type} · 可信度 {v.confidence_bp/100}%</p>):<p>资料不足，不强造应期。</p>}<h3>行动提示</h3><p>{run.report.action_guidance}</p><Link className="product-button" href={`/chronicle/${run.archive_id}`}>查看已保存的三际录</Link><TechnicalDetails><dl className="technical-grid"><div><dt>Core Output Hash</dt><dd><code>{run.core_output_hash}</code></dd></div><div><dt>Report Hash</dt><dd><code>{run.deterministic_report_hash}</code></dd></div><div><dt>Trace Hash</dt><dd><code>{run.trace_hash}</code></dd></div></dl></TechnicalDetails></article></>}
  </ProductShell>
}
