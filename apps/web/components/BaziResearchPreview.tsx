"use client";

import {FormEvent, useState} from "react";

const PROFILES=[
 "BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1",
 "BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1",
 "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
];

type EngineEnvelope={
 id:string;
 banner:string;
 result:{
  output_hash:string;
  trace_hash:string;
  replay_manifest:{content_hash:string};
  module_results:{
   bazi:{
    result:{
     candidate_count:number;
     missing_data:string[];
     candidates:Array<{
      candidate_id:string;
      track_id:string;
      used_local_datetime:string;
      correction_minutes:{total_apparent:string};
      pillars:Record<string,{ganzhi:string}>;
      boundary_flags:Record<string,boolean>;
     }>;
    };
   };
  };
 };
};

export default function BaziResearchPreview(){
 const [profile,setProfile]=useState(PROFILES[0]);
 const [date,setDate]=useState("2024-01-01");
 const [time,setTime]=useState("12:00:00");
 const [unknown,setUnknown]=useState(false);
 const [zone,setZone]=useState("Asia/Shanghai");
 const [longitude,setLongitude]=useState("121.473700");
 const [latitude,setLatitude]=useState("31.230400");
 const [output,setOutput]=useState<EngineEnvelope|null>(null);
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 async function submit(event:FormEvent){
  event.preventDefault();setBusy(true);setError("");setOutput(null);
  const payload={
   profile_id:profile,profile_version:"1.0.0",
   birth_record:{
    local_date:date,local_time:unknown?null:time,calendar_type:"gregorian",
    time_precision:unknown?"unknown":"second",timezone_id:zone,
    place:{latitude,longitude,name:"Owner research input",precision:"user_supplied_coordinates"},
    user_confirmed:true,
   },
   input_provenance:{
    local_date:"user_supplied",local_time:unknown?"explicitly_unknown":"user_supplied",
    timezone_id:"user_supplied",coordinates:"user_supplied",
   },
  };
  try{
   const response=await fetch("/api/v1/admin/research/bazi-four-pillars/execute",{
    method:"POST",credentials:"same-origin",
    headers:{"Content-Type":"application/json","Idempotency-Key":crypto.randomUUID()},
    body:JSON.stringify(payload),
   });
   const body=await response.json();
   if(!response.ok)throw new Error(JSON.stringify(body.detail??body));
   setOutput(body);
  }catch(reason){setError(reason instanceof Error?reason.message:"研究执行失败");}
  finally{setBusy(false);}
 }
 const domain=output?.result.module_results.bazi.result;
 return <section className="panel">
  <h2>Owner 机械排盘预览</h2>
  <form onSubmit={submit}>
   <label>Method Profile<br/><select value={profile} onChange={e=>setProfile(e.target.value)}>
    {PROFILES.map(value=><option key={value}>{value}</option>)}
   </select></label>
   <p><label>出生日期 <input type="date" value={date} onChange={e=>setDate(e.target.value)} required/></label>{" "}
   <label>出生时间 <input type="time" step="1" value={time} disabled={unknown} onChange={e=>setTime(e.target.value)} required={!unknown}/></label>{" "}
   <label><input type="checkbox" checked={unknown} onChange={e=>setUnknown(e.target.checked)}/> 时间未知</label></p>
   <p><label>IANA 时区 <input value={zone} onChange={e=>setZone(e.target.value)} required/></label>{" "}
   <label>经度 <input value={longitude} onChange={e=>setLongitude(e.target.value)} required/></label>{" "}
   <label>纬度 <input value={latitude} onChange={e=>setLatitude(e.target.value)} required/></label></p>
   <button disabled={busy}>{busy?"计算中…":"生成研究候选"}</button>
  </form>
  {error&&<p className="boundary">结构化错误：{error}</p>}
  {output&&domain&&<div>
   <p className="badge">{output.banner}</p>
   <p>候选数：{domain.candidate_count}；缺失：{domain.missing_data.join("、")||"无"}</p>
   {domain.candidates.map(candidate=><article className="panel" key={candidate.candidate_id}>
    <h3>{candidate.candidate_id} · {candidate.track_id}</h3>
    <p>{candidate.used_local_datetime}；视太阳时总校正 {candidate.correction_minutes.total_apparent} 分钟</p>
    <p>年 {candidate.pillars.year.ganzhi}　月 {candidate.pillars.month.ganzhi}　日 {candidate.pillars.day.ganzhi}　时 {candidate.pillars.hour.ganzhi}</p>
    <details><summary>边界敏感性</summary><pre>{JSON.stringify(candidate.boundary_flags,null,2)}</pre></details>
   </article>)}
   <details><summary>版本、哈希与 Replay</summary><pre>{JSON.stringify({
    run_id:output.id,output_hash:output.result.output_hash,trace_hash:output.result.trace_hash,
    replay_manifest_hash:output.result.replay_manifest.content_hash,
   },null,2)}</pre></details>
  </div>}
 </section>;
}
