"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ProductShell, { PageState, TechnicalDetails } from "./ProductShell";
import { apiRequest, readProductSession } from "../lib/product-session";

type EvidenceItem={record_id:string;record_table:string;dimension_id:string;fact_kind:string;withdrawn:boolean;date_precision:string;state:string};
type Candidate={dimension_id:string;rank:number;strength_bp:number;confidence_bp:number;status:string;support_count:number;counterevidence_count:number;missing_facts:string[]};
type Run={id:string;archive_id:string;status:string;strength_bp:number;confidence_bp:number;candidates:Candidate[];output_hash:string;trace_hash:string;research_notice:string};
const labels:Record<string,string>={lx_ming:"命象",lx_ye:"业象",lx_yuan:"愿象",lx_meng:"梦象",lx_yuan_relation:"缘象",lx_shi:"世象"};
const statuses:Record<string,string>={decisive:"象意较明",provisional:"初见其象",contested:"诸象相争",insufficient:"资料不足，暂不成断"};
const missingLabels:Record<string,string>={minimum_independent_records:"独立记录数量不足",minimum_time_span:"记录时间跨度不足"};

export default function LiuxiangReadiness(){
 const [profileId,setProfileId]=useState("");const [items,setItems]=useState<EvidenceItem[]>([]);
 const [excluded,setExcluded]=useState<Set<string>>(new Set());const [run,setRun]=useState<Run>();
 const [state,setState]=useState<"loading"|"ready"|"running"|"error">("loading");const [error,setError]=useState("");
 useEffect(()=>{const id=readProductSession().subject?.id||"";setProfileId(id);if(!id){setState("ready");return}
   apiRequest<{items:EvidenceItem[]}>(`/api/v1/profiles/${id}/liuxiang/evidence`).then(v=>{setItems(v.items);setState("ready")}).catch(e=>{setError(e instanceof Error?e.message:"读取失败");setState("error")})},[]);
 const counts=useMemo(()=>Object.fromEntries(Object.keys(labels).map(id=>[id,items.filter(v=>v.dimension_id===id&&!v.withdrawn).length])),[items]);
 async function executeRun(){setState("running");setError("");try{const result=await apiRequest<Run>(`/api/v1/profiles/${profileId}/liuxiang/executions`,{method:"POST",body:JSON.stringify({excluded_record_ids:[...excluded],title:"六象真实证据研究"})});setRun(result);setState("ready")}catch(e){setError(e instanceof Error?e.message:"执行失败");setState("error")}}
 if(state==="loading")return <ProductShell title="六象资料准备度" eyebrow="合参 · 六象研究"><PageState kind="loading" title="正在读取资料"><p>从加密服务端核对可参与的记录。</p></PageState></ProductShell>;
 return <ProductShell title="六象真实证据研究" eyebrow="合参 · 六象研究" status="research only">
  {!profileId&&<PageState kind="insufficient" title="先建立或选择主体"><p>六象研究只读取你授权主体的资料。</p><Link className="product-button" href="/onboarding">建立主体</Link></PageState>}
  <aside className="privacy-note"><b>研究态声明</b><p>六象是三际观原创研究体系，仍为 UNCONFIRMED 且不可生产激活。易经、八字、紫微到六象的真实映射规则尚未通过审校；出生与机械排盘只影响资料覆盖和可信度，未经审校的干支、星曜、卦象解释继续禁用。普通页面不显示任何合成测试结果。</p></aside>
  {profileId&&<><section className="readiness-list"><div className="product-section-head"><div><h2>本次资料覆盖</h2><p>取消勾选可排除记录；梦境正文、关系正文与出生全文不会进入 Trace。</p></div><span>{items.filter(v=>!v.withdrawn).length} 条可选引用</span></div>
   {Object.entries(labels).map(([id,label],index)=><article key={id}><span aria-hidden="true">{String(index+1).padStart(2,"0")}</span><div><h3>{label}</h3><p>{counts[id]} 条记录；当前只使用明确事实与用户确认标签。</p></div><b>{counts[id]?"已有资料":"尚缺资料"}</b></article>)}
  </section>
  <section className="product-form" aria-label="选择参与证据"><h2>选择本次参与的记录</h2>{items.map(item=><label className="check-field" key={`${item.record_table}:${item.record_id}`}><input type="checkbox" checked={!excluded.has(item.record_id)&&!item.withdrawn} disabled={item.withdrawn} onChange={e=>setExcluded(current=>{const next=new Set(current);e.target.checked?next.delete(item.record_id):next.add(item.record_id);return next})}/><span><b>{labels[item.dimension_id]} · {item.fact_kind==="evidence"?"明确记录":"资料覆盖"}</b><small>{item.date_precision} · {item.state}{item.withdrawn?" · 已撤销":""}</small></span></label>)}
   <button className="product-button" disabled={state==="running"} onClick={executeRun}>{state==="running"?"正在确定性合参…":"执行六象研究"}</button>
  </section></>}
  {error&&<PageState kind="error" title="请求未完成"><p>{error}。资料仍保留在数据库中，可以重试。</p></PageState>}
  {run&&<section className="chronicle-detail"><header><span>{statuses[run.status]||run.status}</span><h2>本次六象结果</h2><p>象势强度 {run.strength_bp} bp · 证据可信度 {run.confidence_bp} bp</p></header>
   {run.candidates.map((item,index)=><section key={item.dimension_id}><span>{String(index+1).padStart(2,"0")}</span><div><h2>{labels[item.dimension_id]} · {statuses[item.status]||item.status}</h2><p>象势强度 {item.strength_bp} bp；证据可信度 {item.confidence_bp} bp；支持 {item.support_count}，逆证 {item.counterevidence_count}。</p>{item.missing_facts.length>0&&<p>尚缺资料：{item.missing_facts.map(v=>missingLabels[v]||"未解释的资料缺口").join("、")}</p>}</div></section>)}
   <p><Link className="product-button" href={`/chronicle/${run.archive_id}`}>查看已保存的三际录</Link></p>
   <TechnicalDetails><dl className="technical-grid"><div><dt>Output Hash</dt><dd><code>{run.output_hash}</code></dd></div><div><dt>Trace Hash</dt><dd><code>{run.trace_hash}</code></dd></div><div><dt>Execution ID</dt><dd><code>{run.id}</code></dd></div></dl></TechnicalDetails>
  </section>}
 </ProductShell>
}
