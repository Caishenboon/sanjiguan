"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import ProductShell, { PageState } from "./ProductShell";
import { apiRequest, newId, readProductSession, updateProductSession } from "../lib/product-session";
import { RECORD_TYPES } from "./RecordCenter";

const allowed = new Set(["dream","vow_action","life_event","reflection","relationship"]);
const apiTypes: Record<string,string> = { dream:"dream", vow_action:"vow_action", life_event:"life_event", reflection:"reflection", relationship:"relationship" };

export default function RecordForm({ requestedType }: { requestedType: string }) {
  const router = useRouter();
  const type = allowed.has(requestedType) ? requestedType : "life_event";
  const info = useMemo(() => RECORD_TYPES.find((item)=>item.id===type)!, [type]);
  const [title,setTitle]=useState("");
  const [date,setDate]=useState(new Date().toISOString().slice(0,10));
  const [dateUnknown,setDateUnknown]=useState(false);
  const [text,setText]=useState("");
  const [status,setStatus]=useState<"idle"|"draft"|"saving"|"error">("idle");
  const [error,setError]=useState("");
  const [profileId,setProfileId]=useState("");
  const [subjectName,setSubjectName]=useState("");

  useEffect(()=>{
    const session=readProductSession();
    setProfileId(session.subject?.id||"");
    setSubjectName(session.subject?.name||"");
  },[]);

  function saveDraft(){
    sessionStorage.setItem(`sanjiguan:draft:${type}`,JSON.stringify({title,date,dateUnknown,text}));
    setStatus("draft");
  }

  async function submit(event:FormEvent){
    event.preventDefault(); setError("");
    if(!profileId){setError("请先建立主体资料。");return}
    if(!title.trim()||!text.trim()){setError("请填写标题和记录内容。");return}
    setStatus("saving");
    try{
      const payload={
        entry_date:dateUnknown?new Date().toISOString().slice(0,10):date,
        entry_type:apiTypes[type],
        fields:{date_precision:dateUnknown?"unknown":"exact_date",record_kind:type},
        free_text:text,
        tags:[],
        evidence_ids:[],
        candidate_evidence:false,
      };
      const response=await apiRequest<{id:string}>(`/api/v1/profiles/${profileId}/journal`,{method:"POST",body:JSON.stringify(payload)});
      const summaryId=response.id||newId("record");
      updateProductSession((session)=>({...session,chronicles:[{
        id:summaryId,profileId,date:dateUnknown?"日期不确定":date,subject:subjectName,type:"记录",
        title:title.trim(),status:"已保存",source:info.title,replayable:false,
      },...session.chronicles],pendingTask:undefined}));
      sessionStorage.removeItem(`sanjiguan:draft:${type}`);
      router.push(`/chronicle?created=${encodeURIComponent(summaryId)}`);
    }catch(cause){
      setStatus("error");
      setError(cause instanceof Error?`保存未完成：${cause.message}。`:"保存未完成，请稍后重试。");
    }
  }

  return <ProductShell title={`记录${info.title}`} eyebrow="记录 · 录一念">
    <div className="form-layout"><form className="product-form" onSubmit={submit}>
      <div className="product-section-head"><div><p className="eyebrow">归入三际录</p><h2>{info.use}</h2></div><span>{info.time}</span></div>
      <label htmlFor="record-title">简短标题 <b>必填</b></label><input id="record-title" value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="以后能一眼认出的标题" required />
      <div className="field-pair"><div><label htmlFor="record-date">发生日期 {!dateUnknown&&<b>必填</b>}</label><input id="record-date" type="date" value={date} onChange={(e)=>setDate(e.target.value)} disabled={dateUnknown}/></div>
      <label className="check-field"><input type="checkbox" checked={dateUnknown} onChange={(e)=>setDateUnknown(e.target.checked)}/><span><b>日期不确定</b><small>保留未知，不自动补成某一天。</small></span></label></div>
      <label htmlFor="record-text">当时发生了什么 <b>必填</b></label><textarea id="record-text" rows={8} value={text} onChange={(e)=>setText(e.target.value)} placeholder="只写你记得或确认的事实；解释和猜测可以另行标注。" required/>
      {type==="relationship"&&<p className="inline-warning">涉及他人时，请使用匿名称呼，或确认对方已同意保存相关资料。</p>}
      {error&&<p className="field-error" role="alert">{error}</p>}
      <div className="form-actions"><Link className="text-button" href="/records">取消</Link><button type="button" className="secondary-button" onClick={saveDraft}>保存草稿</button><button className="product-button" disabled={status==="saving"}>{status==="saving"?"正在保存…":"保存到三际录"}</button></div>
      <p aria-live="polite">{status==="draft"?"草稿仅保留在当前浏览器会话，关闭会话后清除。":""}</p>
    </form><aside className="form-help"><h2>保存后</h2><p>记录会出现在三际录中，并保留原始日期精度。你可以撤回，但系统不会把普通记录自动当作术数证据。</p></aside></div>
    {status==="error"&&<PageState kind="error" title="网络失败，可以重试"><p>页面中的内容仍在。检查连接后再次点击“保存到三际录”。</p></PageState>}
  </ProductShell>;
}
