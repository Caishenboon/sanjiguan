"use client";
import {useState} from "react";
import ProductShell, {TechnicalDetails} from "./ProductShell";

export function TraditionalCompleteResearch(){
 const [result,setResult]=useState<any>(null); const [state,setState]=useState("idle");
 async function run(){setState("loading");try{
  const response=await fetch("/api/v1/admin/research/traditional-complete/execute",{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":crypto.randomUUID()+crypto.randomUUID()},body:JSON.stringify({
   bazi:{local_date:"1990-01-01",local_time:"12:00:00",traditional_sex:"male",yun_sect:1,cycle_count:3,method_profile:{profile_id:"bazi-ziping-complete-v1",version:"1.0.0",sect:1,wall_time_policy:"supplied_local_wall_time"}},
   ziwei:{lunar_year:1990,lunar_month:1,lunar_day:1,hour_index:0,traditional_sex:"male",target_date:"2026-08-03",target_hour_index:0,method_profile:{profile_id:"ziwei-sanhe-complete-v1",version:"1.0.0",leap_month_policy:"iztro_fix_leap_true"}},
   liuyao:{lines:[7,8,9,6,7,8],day_stem_index:0,day_branch_index:0,month_branch_index:6,xunkong_branches:["戌","亥"],question_type:"career",method_profile:{profile_id:"liuyao-jingfang-najia-v1",version:"1.0.0"}}
  })});if(!response.ok)throw new Error(await response.text());setResult(await response.json());setState("done");
 }catch(error){setResult({error:String(error)});setState("error");}}
 const domain=result?.result?.module_results?.["traditional-complete"]?.result;
 return <ProductShell title="传统术数完整 V1" eyebrow="研究与管理 · 固定方法 Profile" status="research only">
  <aside className="privacy-note"><b>研究态 · 未审校</b><p>三套方法各自计算后才进入证据图；结果不代表所有传统流派，也不进入既有档案的静默重算。</p></aside>
  <section className="scope-card"><h2>固定方法</h2><ul><li>八字：子平完整研究 Profile</li><li>紫微：三合基础完整研究 Profile</li><li>六爻：京房纳甲研究 Profile</li></ul><button className="product-button" disabled={state==="loading"} onClick={run}>{state==="loading"?"正在离线计算…":"运行虚构完整案例"}</button></section>
  {state==="error"&&<section className="scope-card"><h2>执行失败</h2><p>请确认 owner 会话、PostgreSQL 与固定上游运行环境可用。</p></section>}
  {domain&&<><section className="scope-card"><h2>合参结果</h2><p>状态：{domain.status}；象势强度：{domain.strength_bp}；证据可信度：{domain.confidence_bp}</p><p>独立来源：{domain.deduplication.independent_source_count}；缺失体系：{domain.missing_systems.join("、")||"无"}</p></section>
  {domain.systems.map((system:any)=><section className="scope-card" key={system.system}><h2>{system.system}</h2><p>Profile：{system.profile_id}</p><p>Ruleset：{system.ruleset_version}</p><p>强度：{system.strength_bp}；可信度：{system.confidence_bp}；状态：{system.status}</p><TechnicalDetails><pre>{JSON.stringify(system.result,null,2)}</pre></TechnicalDetails></section>)}
  <TechnicalDetails><pre>{JSON.stringify({graph_hash:domain.evidence_graph.graph_hash,result_hash:domain.result_hash,warnings:domain.warnings},null,2)}</pre></TechnicalDetails></>}
 </ProductShell>;
}
