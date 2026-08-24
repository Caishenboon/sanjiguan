"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState, TechnicalDetails } from "./ProductShell";
import ObservationInstrument from "./ObservationInstrument";
import { apiRequest } from "../lib/product-session";

const lineNames:Record<string,string>={old_yin:"老阴",young_yang:"少阳",young_yin:"少阴",old_yang:"老阳"};
type ResponseShape={id:string;engine_result?:{lines?:{line_position:number;sum:number;line_state:string;moving:boolean}[];moving_lines?:number[];base_hexagram?:{sequence:number;name:string;key:string};transformed_hexagram?:{sequence:number;name:string;key:string};method_version?:string;mapping_asset?:{asset_version:string}};result_hash?:string;research_status?:string;notice?:string};
type TraditionalRun={mechanical_results:{liuyao?:any};result:{output_hash:string;trace_hash:string;module_results:{"traditional-complete":{result:{systems:Array<{system:string;profile_id:string;ruleset_version:string;result:any}>}}}}};
export default function ResultReader({runId,traditionalRunId}:{runId:string;traditionalRunId?:string}){
 const [payload,setPayload]=useState<ResponseShape>();const [traditional,setTraditional]=useState<TraditionalRun>();const [ready,setReady]=useState(false);
 useEffect(()=>{Promise.allSettled([apiRequest<ResponseShape>(`/api/v1/divinations/${runId}`),traditionalRunId?apiRequest<TraditionalRun>(`/api/v1/traditional-complete/${traditionalRunId}`):Promise.resolve(undefined)]).then(([basic,full])=>{setPayload(basic.status==="fulfilled"?basic.value:undefined);if(full.status==="fulfilled")setTraditional(full.value)}).finally(()=>setReady(true))},[runId,traditionalRunId]);
 if(!ready)return <ProductShell title="读取结果" eyebrow="合参 · 结果"><PageState kind="loading" title="正在读取已保存结果"><p>正在核对当前会话中的执行引用。</p></PageState></ProductShell>
 if(!payload)return <ProductShell title="结果暂不可读" eyebrow="合参 · 结果"><PageState kind="error" title="历史版本无法回放"><p>服务端没有返回这次执行，或当前账号无权读取。</p><Link className="product-button" href="/chronicle">返回三际录</Link></PageState></ProductShell>
 const result=payload.engine_result;
 const liuyao=traditional?.result.module_results["traditional-complete"].result.systems.find(v=>v.system==="liuyao");const complete=liuyao?.result;const mechanical=traditional?.mechanical_results?.liuyao;
 return <ProductShell title="易经三钱机械结果" eyebrow="合参 · 阅读结果" status="机械结构">
  <section className="result-summary"><div><p className="eyebrow">本次完成</p><h2>已按实物三钱记录形成卦象结构</h2><p>这不是吉凶、应期或人生结论。你可以核对六爻、本卦、变卦与动爻，然后在研究详情中查看版本。</p></div><span className="result-kind">机械排盘</span></section>
  <section className="result-primary result-primary--instrument" aria-labelledby="structure-heading"><ObservationInstrument mode="yijing" title={result?.base_hexagram?.name||"本卦"} items={(result?.lines||[]).map(line=>({label:`第${line.line_position}爻`,value:lineNames[line.line_state]||line.line_state,state:line.moving?"moving":"active"}))} caption="六爻自下而上保存；亮点只标记真实动爻，不附加吉凶解释。"/><div><p className="eyebrow">主要结构</p><h2 id="structure-heading">{result?.base_hexagram?.name||"本卦"} → {result?.transformed_hexagram?.name||"变卦"}</h2><dl><div><dt>本卦</dt><dd>第 {result?.base_hexagram?.sequence||"—"} 卦 · {result?.base_hexagram?.name||"未返回"}</dd></div><div><dt>变卦</dt><dd>第 {result?.transformed_hexagram?.sequence||"—"} 卦 · {result?.transformed_hexagram?.name||"未返回"}</dd></div><div><dt>动爻</dt><dd>{result?.moving_lines?.length?result.moving_lines.join("、"):"无"}</dd></div></dl></div>
   <ol className="line-results">{result?.lines?.map((line)=><li key={line.line_position}><span>第 {line.line_position} 爻</span><b>{line.sum} · {lineNames[line.line_state]||line.line_state}</b><small>{line.moving?"动爻":"静爻"}</small></li>)}</ol>
  </section>
  {complete&&<section className="scope-card"><h2>六爻传统结构研究</h2><p>本卦 {mechanical?.primary?.name} · {mechanical?.primary?.palace}宫；世爻 {mechanical?.primary?.shi_position}；应爻 {mechanical?.primary?.ying_position}</p><p>用神候选：{complete.question?.liuqin||"资料不足"}；状态：{complete.question?.status}；结构化吉凶：{complete.verdict}</p><p>动爻：{complete.moving_lines?.join("、")||"无"}；伏吟：{complete.structural_flags?.fuyin_positions?.join("、")||"无"}；反吟：{complete.structural_flags?.fanyin_positions?.join("、")||"无"}</p><p className="inline-warning">此结果属于固定六爻研究 Profile，不等于所有六爻流派的唯一断法。</p></section>}
  <section className="basis-grid"><article><h2>使用了哪些输入</h2><p>一次正式占问、六次实物投掷，按初爻至上爻保存。</p></article><article><h2>哪些内容没有生成</h2><p>没有卦辞解释、吉凶评分、应期、六象映射或 LLM 补写。</p></article></section>
  <div className="result-actions"><Link className="secondary-button" href="/consult">再选一个工具</Link><Link className="product-button" href="/chronicle">查看三际录</Link></div>
  <TechnicalDetails><dl className="technical-grid"><div><dt>Engine version</dt><dd>sanji-engine API 1.0</dd></div><div><dt>Ruleset version</dt><dd>{liuyao?.ruleset_version||"yijing-three-coin-mechanical-0.1.0"}</dd></div><div><dt>Output Hash</dt><dd><code>{traditional?.result.output_hash||payload.result_hash||"由服务端记录"}</code></dd></div><div><dt>Trace Hash</dt><dd><code>{traditional?.result.trace_hash||"在服务端执行记录中保存"}</code></dd></div><div><dt>Profile</dt><dd>{liuyao?.profile_id||"YIJING.THREE_COIN.PHYSICAL.V1"}</dd></div><div><dt>Replay</dt><dd>按原版本重放</dd></div></dl>{complete&&<pre>{JSON.stringify({mechanical,complete},null,2)}</pre>}</TechnicalDetails>
 </ProductShell>
}
