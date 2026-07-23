"use client";
import {useState} from "react";
export default function ResearchLaunch(){
 const [provider,setProvider]=useState("template");const [confirmed,setConfirmed]=useState(false);
 return <section className="panel research-launch"><div><p className="eyebrow">OWNER ONLY</p><h2>封闭研究试算</h2>
  <p>当前不含完整八字、紫微与自动宿世本卦。仅发送脱敏证据摘要；不会发送姓名、邮箱、精确地址、经纬度、关系身份或原始日志。</p></div>
  <fieldset><legend>象辞方式</legend><label className="choice"><input type="radio" name="provider" value="template" checked={provider==="template"} onChange={()=>setProvider("template")}/>三际枢模板 <small>默认 · 不调用外部模型</small></label>
  <label className="choice"><input type="radio" name="provider" value="deepseek" checked={provider==="deepseek"} onChange={()=>setProvider("deepseek")}/>DeepSeek 象辞 <small>发送 verdict、锁定断章及获准摘要</small></label></fieldset>
  <label className="consent"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>我确认以 research_preview 启动；{provider==="deepseek"?"并主动同意本次外部模型调用":"本次仅使用本地模板"}</label>
  <button className="primary-button" disabled={!confirmed}>启动一次研究试算</button>
  <small>不会自动重试、后台重算或定时运行。报告可删除，Token 与费用记录不保存模型原文。</small>
 </section>
}
