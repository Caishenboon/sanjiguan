"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ProductShell, { PageState } from "./ProductShell";
import { apiRequest, readProductSession } from "../lib/product-session";

type Face="heads"|"tails";
type FaceSelection=Face|"";
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
  const [tosses,setTosses]=useState<FaceSelection[][]>(Array.from({length:6},()=>["","",""]));
  const [confirmed,setConfirmed]=useState(false);
  const [questionType,setQuestionType]=useState("general_trend");
  const [dayStemIndex,setDayStemIndex]=useState("0");
  const [monthBranch,setMonthBranch]=useState("子");
  const [dayBranch,setDayBranch]=useState("子");
  const [xunkong,setXunkong]=useState("");
  const [status,setStatus]=useState<"idle"|"saving"|"error">("idle");
  const [error,setError]=useState("");
  useEffect(()=>{const subject=readProductSession().subject;setProfileId(subject?.id||"");},[]);
  function setFace(line:number,coin:number,value:FaceSelection){setTosses(current=>current.map((row,i)=>i===line?row.map((v,j)=>j===coin?value:v):row))}
  async function submit(event:FormEvent){
    event.preventDefault();setError("");
    if(!profileId){setError("请先建立主体资料。");return}
    if(!question.trim()||!confirmed||tosses.some(row=>row.some(face=>!face))){setError("请填写占问、逐枚录入六次实物投掷，并完成确认。");return}
    setStatus("saving");
    try{
      const response=await apiRequest<Response>(`/api/v1/profiles/${profileId}/divinations/three-coin`,{method:"POST",body:JSON.stringify({
        question:question.trim(),purpose,divination_at:new Date().toISOString(),timezone:"Asia/Shanghai",location_precision:"none",
        method_id:"YIJING.THREE_COIN.PHYSICAL.V1",coin_face_mapping_id:"COIN_FACES.HEADS_3_TAILS_2.V1",coin_face_mapping_version:"1.0.0",
        tosses:tosses.map((coin_faces,index)=>({line_no:index+1,coin_faces:coin_faces as Face[],was_retossed:false})),
        interrupted_retoss:false,repeated_due_to_dissatisfaction:false,method_version:"1.0.0",
      })});
      const traditional=await apiRequest<{id:string}>("/api/v1/traditional-complete/execute",{method:"POST",body:JSON.stringify({profile_record_id:profileId,liuyao:{
        lines:response.engine_result.lines.map(line=>line.sum),day_stem_index:Number(dayStemIndex),month_branch:monthBranch,day_branch:dayBranch,
        xunkong_branches:xunkong.split(/[、,\s]+/).filter(Boolean),question_type:questionType,
        method_profile:{profile_id:"liuyao-jingfang-najia-v1",version:"1.0.0"}
      }})});
      router.push(`/results/${response.id}?traditional=${traditional.id}`);
    }catch(cause){setStatus("error");setError(cause instanceof Error?`执行未完成：${cause.message}。`:"执行未完成，请检查网络后重试。")}
  }
  if(!profileId)return <ProductShell title="易经三钱" eyebrow="合参 · 机械排盘"><PageState kind="insufficient" title="需要先建立主体"><p>占问记录必须归入一个主体档案。</p><Link className="product-button" href="/onboarding">建立主体</Link></PageState></ProductShell>
  return <ProductShell title="录入实物三钱" eyebrow="合参 · 易经机械排盘" status="research_active">
    <div className="form-layout"><form className="product-form" onSubmit={submit}><div className="product-section-head"><div><h2>六爻自下而上录入</h2><p>系统不随机投掷，也不会因为结果不满意而自动重来。</p></div><span>约 5 分钟</span></div>
      <label htmlFor="question">这次正式占问什么 <b>必填</b></label><textarea id="question" rows={3} value={question} onChange={(e)=>setQuestion(e.target.value)} required/>
      <label htmlFor="purpose">占问目的 <b>必填</b></label><input id="purpose" value={purpose} onChange={(e)=>setPurpose(e.target.value)}/>
      <label htmlFor="question-type">问题类型 Profile <b>必填</b></label><select id="question-type" value={questionType} onChange={e=>setQuestionType(e.target.value)}><option value="general_trend">一般趋势（不自动选用神）</option><option value="self">自身</option><option value="career">事业</option><option value="wealth">财务</option><option value="relationship">关系</option><option value="travel">出行</option><option value="study">学业</option><option value="lost_property">失物</option></select>
      <div className="field-pair"><div><label htmlFor="day-stem-index">日干序号（甲=0） <b>必填</b></label><input id="day-stem-index" type="number" min="0" max="9" value={dayStemIndex} onChange={e=>setDayStemIndex(e.target.value)}/></div><div><label htmlFor="xunkong">旬空地支</label><input id="xunkong" value={xunkong} onChange={e=>setXunkong(e.target.value)} placeholder="例如：戌、亥；未知可留空"/></div></div>
      <div className="field-pair"><label>月建地支<select value={monthBranch} onChange={e=>setMonthBranch(e.target.value)}>{"子丑寅卯辰巳午未申酉戌亥".split("").map(v=><option key={v}>{v}</option>)}</select></label><label>日辰地支<select value={dayBranch} onChange={e=>setDayBranch(e.target.value)}>{"子丑寅卯辰巳午未申酉戌亥".split("").map(v=><option key={v}>{v}</option>)}</select></label></div>
      <fieldset className="coin-fieldset"><legend>六次投掷结果 <b>必填</b></legend><p>Canonical 数值契约为每枚钱 2 或 3；钱面称呼只是当前 Profile 的显示标签。</p>{tosses.map((row,line)=><div className="coin-row" key={line}><strong>{lineNames[line]}</strong>{row.map((face,coin)=><label key={coin}>第 {coin+1} 枚<select aria-label={`${lineNames[line]}第${coin+1}枚`} value={face} onChange={(e)=>setFace(line,coin,e.target.value as FaceSelection)} required><option value="">请选择</option><option value="tails">2（反面）</option><option value="heads">3（正面）</option></select></label>)}</div>)}</fieldset>
      <label className="check-field"><input type="checkbox" checked={confirmed} onChange={(e)=>setConfirmed(e.target.checked)}/><span><b>我确认这是一次正式实物投掷</b><small>结果将按原始币面保存，可按原版本重放。</small></span></label>
      {error&&<p role="alert" className="field-error">{error}</p>}
      <div className="form-actions"><Link className="text-button" href="/consult">取消</Link><button className="product-button" disabled={status==="saving"}>{status==="saving"?"正在形成机械结构…":"形成机械结构"}</button></div>
    </form><aside className="form-help"><h2>本次会得到</h2><ul><li>六爻 6 / 7 / 8 / 9</li><li>本卦、变卦、八宫与世应</li><li>纳甲、六亲、六神与动爻</li><li>月日、旬空、飞伏神和用神候选</li><li>可回放的 Profile、Ruleset 与 Hash</li></ul><p>结构化断法保持研究态，不代表所有六爻流派共识。</p></aside></div>
    {status==="error"&&<PageState kind="error" title="网络失败，可以重试"><p>输入仍保留在页面。系统不会在失败时生成占位卦象。</p></PageState>}
  </ProductShell>
}
