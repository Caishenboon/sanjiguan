"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState, TechnicalDetails } from "./ProductShell";
import { apiRequest, readProductSession } from "../lib/product-session";
import { epistemicDisplay, productStatus } from "../lib/product-language";

type Topic = "sushe" | "zhongyin_life" | "zhongyin_deceased" | "yuanqi";
type Epistemic<T=unknown>={value:T;epistemic_status:string;confidence_bp:number};
type Candidate={
  candidate_id:string;rank:number;strength_bp:number;confidence_bp:number;status:string;
  name?:Epistemic<string>;active_era?:Epistemic<string>;region_candidates?:Epistemic<string[]>;
  identity?:Epistemic<string>;profession?:Epistemic<string>;key_life_events?:Epistemic<string>;
  death_candidates?:Array<{rank:number;cause:Epistemic<string>}>;
  reincarnation?:{main_value:Epistemic<number>;range:Epistemic<number[]>};
  causal_debts?:Array<{debt_id:string;type:Epistemic<string>;confidence_bp:number}>;
  transition_state?:Epistemic<string>;old_structure?:Epistemic<string[]>;
  new_structure_clues?:Epistemic<string[]>;unfinished_matters?:Epistemic<string[]>;
  observation_scope?:string;relationship_stage?:Epistemic<string>;
  future_trend?:Epistemic<string>;past_life_identity_candidates?:Array<{side:string;name:Epistemic<string>}>;
  supporting_record_ids:string[];counterevidence_record_ids:string[];conflicts:string[];missing_facts:string[];
};
type Run={id:string;archive_id:string;topic_type:Topic;status:string;strength_bp:number;confidence_bp:number;candidates:Candidate[];graph_hash:string;output_hash:string;trace_hash:string;research_notice:string};
type Evidence={record_id:string;node_type:string;tags:string[];withdrawn:boolean};

const COPY={
  sushe:{title:"宿世观",intro:"三际观原创的确定性研究候选，不是历史身份认定。所有推演字段均带认识状态。"},
  zhongyin_life:{title:"中阴观 · 人生过渡",intro:"观察旧结构消散与新结构形成之间的过渡，不预测死亡。"},
  zhongyin_deceased:{title:"中阴观 · 离世过渡研究",intro:"仅对已有明确离世记录的主体开放；主观感受不升级为客观灵界事实。"},
  yuanqi:{title:"缘契观",intro:"区分单方关系观察与双方允许合参，不判断命定伴侣或必然复合。"},
} as const;

function ep(value?:Epistemic<unknown>){
  if(!value)return "【可能·资料不足】";
  const shown=Array.isArray(value.value)?value.value.join("、"):String(value.value);
  return epistemicDisplay(shown,value.epistemic_status,value.confidence_bp);
}

export default function TopicResearch({topic}: {topic:Topic}){
  const [mode,setMode]=useState<Topic>(topic);
  const [profileId,setProfileId]=useState(""); const [items,setItems]=useState<Evidence[]>([]);
  const [excluded,setExcluded]=useState<Set<string>>(new Set()); const [run,setRun]=useState<Run>();
  const [state,setState]=useState<"loading"|"ready"|"running"|"error">("loading"); const [error,setError]=useState("");
  useEffect(()=>{const id=readProductSession().subject?.id||"";setProfileId(id);if(!id){setState("ready");return}
    apiRequest<{items:Evidence[]}>(`/api/v1/profiles/${id}/topics/${mode}/evidence`).then(v=>{setItems(v.items);setState("ready")}).catch(e=>{setError(e instanceof Error?e.message:"读取失败");setState("error")})},[mode]);
  async function runTopic(){setState("running");setError("");try{setRun(await apiRequest<Run>(`/api/v1/profiles/${profileId}/topics/${mode}/executions`,{method:"POST",body:JSON.stringify({excluded_record_ids:[...excluded],title:COPY[mode].title})}));setState("ready")}catch(e){setError(e instanceof Error?e.message:"执行失败");setState("error")}}
  if(state==="loading")return <ProductShell title={COPY[mode].title} eyebrow="合参 · 专题研究"><PageState kind="loading" title="正在读取授权资料"><p>只读取结构标签和记录引用，不把敏感正文写入专题图。</p></PageState></ProductShell>;
  return <ProductShell title={COPY[mode].title} eyebrow="合参 · 专题研究" status="research only">
    <aside className="privacy-note"><b>三际观原创研究 · UNCONFIRMED</b><p>{COPY[mode].intro} 这些规则不可生产激活，也不使用 DeepSeek 或 Oracle 计算。</p></aside>
    {topic.startsWith("zhongyin")&&<div className="tool-head" aria-label="中阴观模式"><button className="product-button" aria-pressed={mode==="zhongyin_life"} onClick={()=>{setRun(undefined);setMode("zhongyin_life")}}>人生过渡中阴</button><button className="product-button secondary" aria-pressed={mode==="zhongyin_deceased"} onClick={()=>{setRun(undefined);setMode("zhongyin_deceased")}}>离世过渡研究</button></div>}
    {!profileId&&<PageState kind="insufficient" title="先建立或选择主体"><p>专题推演只读取你授权主体的记录。</p><Link className="product-button" href="/onboarding">建立主体</Link></PageState>}
    {profileId&&<section className="product-form" aria-label="专题资料选择"><h2>选择本次参与的资料</h2><p>{items.length} 条结构引用可用；撤销记录不会进入新执行。</p>
      {items.map(item=><label className="check-field" key={item.record_id}><input type="checkbox" checked={!excluded.has(item.record_id)&&!item.withdrawn} disabled={item.withdrawn} onChange={e=>setExcluded(old=>{const next=new Set(old);e.target.checked?next.delete(item.record_id):next.add(item.record_id);return next})}/><span><b>{item.node_type}</b><small>{item.tags.join("、")||"资料覆盖"}{item.withdrawn?" · 已撤销":""}</small></span></label>)}
      <button className="product-button" disabled={state==="running"} onClick={runTopic}>{state==="running"?"正在确定性推演…":"开始专题推演"}</button>
    </section>}
    {error&&<PageState kind="error" title="本次执行未完成"><p>{error}。已有记录没有被覆盖，可检查资料后重试。</p></PageState>}
    {run&&<section className="chronicle-detail"><header><span>{productStatus(run.status)}</span><h2>确定性专题结果</h2><p>象势强度 {run.strength_bp} bp · 证据可信度 {run.confidence_bp} bp</p></header>
      {run.candidates.map((item,index)=><section key={item.candidate_id}><span>{String(index+1).padStart(2,"0")}</span><div>
        {item.name&&<h2>{ep(item.name)}</h2>}
        {!item.name&&<h2>候选 {item.rank} · {productStatus(item.status)}</h2>}
        {mode==="sushe"&&<><p>年代：{ep(item.active_era)}；地点：{ep(item.region_candidates)}</p><p>身份：{ep(item.identity)}；职业：{ep(item.profession)}</p><p>关键经历：{ep(item.key_life_events)}</p><p>死因候选：{item.death_candidates?.map(v=>ep(v.cause)).join("、")}</p><p>轮回序位：{ep(item.reincarnation?.main_value)}；范围：{ep(item.reincarnation?.range)}</p><p>因果债务：{item.causal_debts?.map(v=>ep(v.type)).join("、")}</p></>}
        {mode.startsWith("zhongyin")&&<><p>当前过渡：{ep(item.transition_state)}</p><p>旧结构：{ep(item.old_structure)}；新结构线索：{ep(item.new_structure_clues)}</p><p>未完成事项：{ep(item.unfinished_matters)}</p></>}
        {mode==="yuanqi"&&<><p>{item.observation_scope==="bilateral_structure"?"双向关系结构":"基于单方记录的缘契观察"}</p><p>关系阶段：{ep(item.relationship_stage)}；趋势：{ep(item.future_trend)}</p><p>宿世推演姓名：{item.past_life_identity_candidates?.map(v=>ep(v.name)).join("、")}</p></>}
        <p>支持 {item.supporting_record_ids.length} · 逆证 {item.counterevidence_record_ids.length} · 冲突 {item.conflicts.length} · 尚缺 {item.missing_facts.length}</p>
        <p>象势强度 {item.strength_bp} bp；证据可信度 {item.confidence_bp} bp。</p>
      </div></section>)}
      <p><Link className="product-button" href={`/chronicle/${run.archive_id}`}>查看已保存的三际录</Link></p>
      <TechnicalDetails><dl className="technical-grid"><div><dt>Graph Hash</dt><dd><code>{run.graph_hash}</code></dd></div><div><dt>Output Hash</dt><dd><code>{run.output_hash}</code></dd></div><div><dt>Trace Hash</dt><dd><code>{run.trace_hash}</code></dd></div></dl></TechnicalDetails>
    </section>}
  </ProductShell>;
}
