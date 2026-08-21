"use client";

import Link from "next/link";
import {useEffect,useState} from "react";
import ProductShell,{MetricPair,PageState,TechnicalDetails} from "./ProductShell";
import {apiRequest,readProductSession} from "../lib/product-session";

type Birth={calendar_type:string;local_date:string;local_time:string|null;timezone_id:string;time_precision:string;place:{longitude:number}};
type Profile={id:string;birth?:Birth|null;birth_record_status:string};
type Run={id:string;mechanical_results:{bazi?:any};result:{output_hash:string;trace_hash:string;module_results:{"traditional-complete":{result:{systems:Array<{system:string;profile_id:string;ruleset_version:string;strength_bp:number;confidence_bp:number;status:string;result:any}>;status:string;warnings:string[]}}}}};

export default function BaziCompleteJourney(){
 const [profile,setProfile]=useState<Profile|null>(null);const [sex,setSex]=useState("male");
 const [run,setRun]=useState<Run|null>(null);const [state,setState]=useState<"loading"|"idle"|"running"|"error">("loading");const [error,setError]=useState("");
 useEffect(()=>{const id=readProductSession().subject?.id;if(!id){setState("idle");return}apiRequest<Profile>(`/api/v1/profiles/${id}`).then(v=>{setProfile(v);setState("idle")}).catch(e=>{setError(String(e));setState("error")})},[]);
 async function execute(){if(!profile?.birth?.local_time)return;if(profile.birth.calendar_type!=="gregorian"){setError("当前研究 Profile 只接受已确认的公历日期；不会把其他历法静默当作公历。");setState("error");return}setState("running");setError("");try{setRun(await apiRequest<Run>("/api/v1/traditional-complete/execute",{method:"POST",body:JSON.stringify({profile_record_id:profile.id,bazi:{local_date:profile.birth.local_date,local_time:profile.birth.local_time,calendar_type:profile.birth.calendar_type,timezone_id:profile.birth.timezone_id,longitude:String(profile.birth.place.longitude),traditional_sex:sex,yun_sect:1,cycle_count:10,method_profile:{profile_id:"bazi-ziping-complete-v1",version:"1.0.0",sect:1,wall_time_policy:"supplied_local_wall_time"}}})}));setState("idle")}catch(e){setError(e instanceof Error?e.message:String(e));setState("error")}}
 if(state==="loading")return <ProductShell title="八字传统结构" eyebrow="合参 · 八字"><PageState kind="loading" title="正在读取主体资料"><p>只从服务端读取已确认原始记录。</p></PageState></ProductShell>;
 if(!profile)return <ProductShell title="八字传统结构" eyebrow="合参 · 八字"><PageState kind="insufficient" title="请先建立主体"><Link className="product-button" href="/onboarding">建立主体</Link></PageState></ProductShell>;
 if(!profile.birth||!profile.birth.local_time)return <ProductShell title="八字传统结构" eyebrow="合参 · 八字"><PageState kind="insufficient" title="出生时刻未知，暂不生成完整四柱"><p>系统不会补造时辰。可先完善资料，或继续使用未知时辰的候选研究。</p><Link className="product-button" href="/onboarding">完善资料</Link></PageState></ProductShell>;
 const system=run?.result.module_results["traditional-complete"].result.systems.find(v=>v.system==="bazi");const result=system?.result;const mechanical=run?.mechanical_results?.bazi;
 return <ProductShell title="八字传统结构" eyebrow="合参 · 八字" status="研究中 · 尚未审校"><aside className="privacy-note"><b>固定研究方法，不代表所有八字流派共识</b><p>结构与候选由确定性引擎生成；DeepSeek 不参与。旺衰、格局、调候和用神仍是该方法下的研究候选。</p></aside><section className="product-form"><label>传统性别参数<select value={sex} onChange={e=>setSex(e.target.value)}><option value="male">男</option><option value="female">女</option></select></label><button className="product-button" disabled={state==="running"} onClick={execute}>{state==="running"?"正在计算…":"按当前研究方法排盘"}</button>{error&&<p role="alert" className="field-error">{error}</p>}</section>{system&&<><section className="scope-card"><h2>四柱与传统结构</h2><p>{Object.values(mechanical?.pillars||{}).join("　")}</p><MetricPair strengthBp={system.strength_bp} confidenceBp={system.confidence_bp}/><p>当前状态：{system.status}</p><h3>旺衰研究证据</h3><p>{result.strength?.status} · 平衡基点 {result.strength?.balance_bp}</p><h3>格局与用神研究候选</h3><p>{result.pattern?.candidate} · {result.useful_elements?.candidates?.join("、")}</p></section><TechnicalDetails><pre>{JSON.stringify({profile:system.profile_id,ruleset:system.ruleset_version,mechanical,result,output_hash:run?.result.output_hash,trace_hash:run?.result.trace_hash},null,2)}</pre></TechnicalDetails></>}</ProductShell>;
}
