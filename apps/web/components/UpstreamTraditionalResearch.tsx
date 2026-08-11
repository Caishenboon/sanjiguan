"use client";
import {useState} from "react";
import ProductShell, {TechnicalDetails} from "./ProductShell";

export function UpstreamTraditionalResearch(){
 const [result,setResult]=useState<any>(null); const [state,setState]=useState("idle");
 async function run(){setState("loading");setResult(null);try{
  const response=await fetch("/api/v1/admin/research/upstream-traditional/execute",{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":crypto.randomUUID()+crypto.randomUUID()},body:JSON.stringify({
   bazi:{local_date:"1990-01-01",local_time:"12:00:00",traditional_sex:"male",yun_sect:1,cycle_count:3,method_profile:{profile_id:"lunar-python-sect1",version:"1.0.0",sect:1,wall_time_policy:"supplied_local_wall_time"}},
   ziwei:{lunar_year:1990,lunar_month:1,lunar_day:1,hour_index:0,traditional_sex:"male",target_date:"2026-08-03",target_hour_index:0,method_profile:{profile_id:"iztro-lunar-standard",version:"2.5.8",leap_month_policy:"iztro_fix_leap_true"}},
   liuyao:{lines:[7,8,9,6,7,8],day_stem_index:0,method_profile:{profile_id:"yaomancy-liuyao-engine-0.1.0",version:"1.0.0"}}
  })});if(!response.ok)throw new Error(await response.text());setResult(await response.json());setState("done");
 }catch(error){setState("error");setResult({error:String(error)});}}
 const domain=result?.result?.module_results?.upstream?.result;
 return <ProductShell title="传统机械上游对照" eyebrow="研究与管理 · 固定版本" status="research only">
  <aside className="privacy-note"><b>研究态 · 未审校</b><p>开源上游只提供固定版本机械结构，不代表唯一正统，也不直接形成吉凶、用神或最终断语。</p></aside>
  <section className="scope-card"><h2>当前固定来源</h2><ul><li>八字：lunar-python 1.4.8</li><li>紫微：iztro 2.5.8</li><li>六爻：liuyao-engine 0.1.0 机械装卦</li></ul><button className="product-button" disabled={state==="loading"} onClick={run}>{state==="loading"?"正在离线计算…":"运行虚构对照案例"}</button></section>
  {state==="error"&&<section className="scope-card"><h2>执行失败</h2><p>请确认 owner 会话、PostgreSQL 和固定上游运行环境可用。</p></section>}
  {domain&&<section className="scope-card"><h2>结构结果</h2><p>状态：资料不足，暂不成断</p><p>独立上游：{domain.deduplication.independent_source_count}；象势强度：0；证据可信度：0。</p><p>没有审校通过的解释映射，因此机械事实不会被换算为评分。</p><TechnicalDetails><pre>{JSON.stringify({ruleset:domain.ruleset_version,graph_hash:domain.evidence_graph.graph_hash,disputes:domain.disputes,adapters:domain.adapter_results.map((x:any)=>({name:x.upstream_name,version:x.upstream_version,commit:x.upstream_commit,hash:x.canonical_hash}))},null,2)}</pre></TechnicalDetails></section>}
 </ProductShell>;
}
