"use client";
import {useState} from "react";

type Line={line_position:number;coin_values:number[];sum:number;line_state:string;moving:boolean};
type EngineResult={input_order:string;lines:Line[];moving_lines:number[];
 lower_trigram:{name:string};upper_trigram:{name:string};
 base_hexagram:{sequence:number;name:string;key:string};
 transformed_hexagram:{sequence:number;name:string;key:string};
 has_transformed_hexagram:boolean;method_version:string;
 mapping_asset:{asset_version:string}};
const labels:Record<string,string>={
 old_yin:"老阴",young_yang:"少阳",young_yin:"少阴",old_yang:"老阳"
};

export default function ThreeCoinPreview(){
 const [id,setId]=useState("");const [result,setResult]=useState<EngineResult|null>(null);
 const [hash,setHash]=useState("");const [status,setStatus]=useState("");const [error,setError]=useState("");
 async function load(){
  setError("");setResult(null);
  const response=await fetch(`/api/v1/divinations/${encodeURIComponent(id)}`,{credentials:"include"});
  if(!response.ok){setError("无法读取该记录，或当前会话无权查看。");return}
  const payload=await response.json();
  if(!payload.engine_result){setStatus("legacy_method_unknown");setError("旧记录缺少完整币面映射，不能自动补算。");return}
  setResult(payload.engine_result);setHash(payload.result_hash);setStatus(payload.research_status);
 }
 return <section className="panel"><h2>读取实物三钱记录</h2>
  <label>起卦记录 ID<input value={id} onChange={event=>setId(event.target.value)}/></label>
  <button className="primary-button" onClick={load} disabled={!id}>载入确定性卦象</button>
  {error&&<p role="alert">{error}</p>}
  {result&&<div><p>爻序：初爻至上爻（自下而上） · 研究状态：{status}</p>
   <ol>{result.lines.map(line=><li key={line.line_position}>第 {line.line_position} 爻：
    [{line.coin_values.join(", ")}] → {line.sum} · {labels[line.line_state]}
    {line.moving?" · 动爻":""}</li>)}</ol>
   <p>下卦：{result.lower_trigram.name}　上卦：{result.upper_trigram.name}</p>
   <p>本卦：第 {result.base_hexagram.sequence} 卦 {result.base_hexagram.name}（{result.base_hexagram.key}）</p>
   <p>变卦：第 {result.transformed_hexagram.sequence} 卦 {result.transformed_hexagram.name}（{result.transformed_hexagram.key}）</p>
   <p>动爻：{result.moving_lines.length?result.moving_lines.join("、"):"无"} ·
    是否存在变化：{result.has_transformed_hexagram?"是":"否"}</p>
   <p>方法版本：{result.method_version} · 映射资产：{result.mapping_asset.asset_version}</p>
   <p>结果哈希：<code>{hash}</code></p></div>}
 </section>
}
