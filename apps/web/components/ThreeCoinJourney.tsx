"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ProductShell, { PageState } from "./ProductShell";
import { apiRequest, readProductSession } from "../lib/product-session";

type Face="heads"|"tails";
type EngineResult={
  lines:{line_position:number;sum:number;line_state:string;moving:boolean}[];
  moving_lines:number[];
  base_hexagram:{sequence:number;name:string;key:string};
  transformed_hexagram:{sequence:number;name:string;key:string};
  method_version:string;
  mapping_asset:{asset_version:string};
};
type Response={id:string;engine_result:EngineResult;result_hash:string;research_status:string;notice:string};

const lineNames=["初爻","二爻","三爻","四爻","五爻","上爻"];

export default function ThreeCoinJourney(){
  const router=useRouter();
  const [profileId,setProfileId]=useState("");
  const [question,setQuestion]=useState("");
  const [purpose,setPurpose]=useState("记录一次正式占问");
  const [tosses,setTosses]=useState<Face[][]>(Array.from({length:6},()=>["heads","tails","heads"]));
  const [confirmed,setConfirmed]=useState(false);
  const [status,setStatus]=useState<"idle"|"saving"|"error">("idle");
  const [error,setError]=useState("");
  useEffect(()=>{const subject=readProductSession().subject;setProfileId(subject?.id||"");},[]);
  function setFace(line:number,coin:number,value:Face){setTosses(current=>current.map((row,i)=>i===line?row.map((v,j)=>j===coin?value:v):row))}
  async function submit(event:FormEvent){
    event.preventDefault();setError("");
    if(!profileId){setError("请先建立主体资料。");return}
    if(!question.trim()||!confirmed){setError("请填写占问，并确认六次结果来自实物投掷。");return}
    setStatus("saving");
    try{
      const response=await apiRequest<Response>(`/api/v1/profiles/${profileId}/divinations/three-coin`,{method:"POST",body:JSON.stringify({
        question:question.trim(),purpose,divination_at:new Date().toISOString(),timezone:"Asia/Shanghai",location_precision:"none",
        method_id:"YIJING.THREE_COIN.PHYSICAL.V1",coin_face_mapping_id:"COIN_FACES.HEADS_3_TAILS_2.V1",coin_face_mapping_version:"1.0.0",
        tosses:tosses.map((coin_faces,index)=>({line_no:index+1,coin_faces,was_retossed:false})),
        interrupted_retoss:false,repeated_due_to_dissatisfaction:false,method_version:"1.0.0",
      })});
      router.push(`/results/${response.id}`);
    }catch(cause){setStatus("error");setError(cause instanceof Error?`执行未完成：${cause.message}。`:"执行未完成，请检查网络后重试。")}
  }
  if(!profileId)return <ProductShell title="易经三钱" eyebrow="合参 · 机械排盘"><PageState kind="insufficient" title="需要先建立主体"><p>占问记录必须归入一个主体档案。</p><Link className="product-button" href="/onboarding">建立主体</Link></PageState></ProductShell>
  return <ProductShell title="录入实物三钱" eyebrow="合参 · 易经机械排盘" status="research_active">
    <div className="form-layout"><form className="product-form" onSubmit={submit}><div className="product-section-head"><div><h2>六爻自下而上录入</h2><p>系统不随机投掷，也不会因为结果不满意而自动重来。</p></div><span>约 5 分钟</span></div>
      <label htmlFor="question">这次正式占问什么 <b>必填</b></label><textarea id="question" rows={3} value={question} onChange={(e)=>setQuestion(e.target.value)} required/>
      <label htmlFor="purpose">占问目的 <b>必填</b></label><input id="purpose" value={purpose} onChange={(e)=>setPurpose(e.target.value)}/>
      <fieldset className="coin-fieldset"><legend>六次投掷结果 <b>必填</b></legend>{tosses.map((row,line)=><div className="coin-row" key={line}><strong>{lineNames[line]}</strong>{row.map((face,coin)=><label key={coin}>第 {coin+1} 枚<select aria-label={`${lineNames[line]}第${coin+1}枚`} value={face} onChange={(e)=>setFace(line,coin,e.target.value as Face)}><option value="heads">正面（3）</option><option value="tails">反面（2）</option></select></label>)}</div>)}</fieldset>
      <label className="check-field"><input type="checkbox" checked={confirmed} onChange={(e)=>setConfirmed(e.target.checked)}/><span><b>我确认这是一次正式实物投掷</b><small>结果将按原始币面保存，可按原版本重放。</small></span></label>
      {error&&<p role="alert" className="field-error">{error}</p>}
      <div className="form-actions"><Link className="text-button" href="/consult">取消</Link><button className="product-button" disabled={status==="saving"}>{status==="saving"?"正在形成机械结构…":"形成机械结构"}</button></div>
    </form><aside className="form-help"><h2>本次会得到</h2><ul><li>六爻 6 / 7 / 8 / 9</li><li>本卦与变卦</li><li>动爻位置</li><li>可回放的版本和哈希</li></ul><p>不会得到卦辞解释、吉凶评分或应期。</p></aside></div>
    {status==="error"&&<PageState kind="error" title="网络失败，可以重试"><p>输入仍保留在页面。系统不会在失败时生成占位卦象。</p></PageState>}
  </ProductShell>
}
