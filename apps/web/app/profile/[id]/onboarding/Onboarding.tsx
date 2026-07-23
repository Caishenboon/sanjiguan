"use client";
import { useEffect, useState } from "react";

const steps = [
  ["立卷","档案称呼、语言与长期保存选择"],["生时","原始出生时间、历法、地点与精度"],
  ["梦象","反复梦境"],["感应象","身体、环境与时间相关的反复感受"],
  ["业象","长期习惯、困扰与可观察反例"],["愿象","愿心、承诺与已经采取的行动"],
  ["缘象","仅记录已同意的对象，或完全匿名的事件"],["世象","重要人生事件与时间线"],
] as const;

export default function Onboarding({profileId}:{profileId:string}) {
  const storageKey=`sanjiguan:onboarding:${profileId}`;
  const [step,setStep]=useState(1), [answer,setAnswer]=useState("later"), [note,setNote]=useState("");
  useEffect(()=>{const saved=localStorage.getItem(storageKey);if(saved){const v=JSON.parse(saved);setStep(v.step||1);setAnswer(v.answer||"later");setNote(v.note||"");}},[storageKey]);
  useEffect(()=>{localStorage.setItem(storageKey,JSON.stringify({step,answer,note}));},[storageKey,step,answer,note]);
  return <main className="shell">
    <p className="eyebrow">八步立卷 · 自动保存于当前设备</p>
    <h1>{step}. {steps[step-1][0]}</h1><p>{steps[step-1][1]}</p>
    <label>回答状态<select value={answer} onChange={e=>setAnswer(e.target.value)}>
      <option value="complete">已填写</option><option value="unknown">不知道</option>
      <option value="explicit_none">明确没有</option><option value="not_applicable">不适用</option>
      <option value="later">稍后填写</option>
    </select></label>
    <label>原始记录<textarea rows={8} value={note} onChange={e=>setNote(e.target.value)}
      placeholder="如实记录；系统不会自动推断术数结论。" /></label>
    <div className="actions"><button disabled={step===1} onClick={()=>setStep(step-1)}>上一步</button>
      <button disabled={step===8} onClick={()=>setStep(step+1)}>保存并继续</button></div>
    <p className="boundary">可随时退出后继续。正式登录后由加密 API 保存；本页不生成任何命理结论。</p>
  </main>;
}
