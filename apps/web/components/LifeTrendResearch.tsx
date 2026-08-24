"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState, TechnicalDetails, VerdictBanner } from "./ProductShell";
import { apiRequest, readProductSession } from "../lib/product-session";
import { productStatus } from "../lib/product-language";

type Candle = { open:number; high:number; low:number; close:number };
type Bucket = { bucket_id:string; start:string; end:string; segment:string; candle:Candle|null; confidence_bp:number; coverage_bp:number; status:string; auspice:{label:string}; missing:string[] };
type Window = { window_id:string; start:string; end:string; type:string; confidence_bp:number };
type Report = { chapter:string; symbolic_title:string; image_text:string; plain_interpretation:string; past:string; current:string; future:string; auspice:string; action_guidance:string };
type Run = { id:string; archive_id:string; status:string; timeline:Bucket[]; timing_windows:Window[]; report:Report; core_output_hash:string; deterministic_report_hash:string; trace_hash:string };
type Evidence = { factor_id:string; factor_type:string; occurred_on:string|null; tags:string[] };

const SEGMENT: Record<string,string> = { observed_past:"往际事实", current_state:"当下", projected_future:"未来推演", insufficient_gap:"资料留白" };
const WINDOW_LABELS: Record<string,string> = { action_window:"行动窗口", relationship_window:"关系窗口", transition_window:"过渡窗口", obstruction_window:"阻滞窗口", completion_window:"完成窗口" };

function Trend({ values }: { values:Bucket[] }) {
  const points = values.filter((value) => value.candle);
  if (!points.length) return <PageState kind="insufficient" title="证契未足，暂不绘制命势"><p>空白时间段不会被随机插值或补造。补充带时间精度的人生事件后可以重观。</p></PageState>;
  const x = (index:number) => 24 + index * (552 / Math.max(1, points.length - 1));
  const y = (value:number) => 120 - (value / 10000) * 92;
  const path = points.map((value,index) => `${index ? "L" : "M"} ${x(index)} ${y(value.candle!.close)}`).join(" ");
  return <figure className="trend-figure">
    <div className="trend-legend" aria-label="命势图例"><span><i/>已有记录</span><span className="future"><i/>未来推演</span><span className="gap"><i/>资料留白</span></div>
    <svg viewBox="0 0 600 240" role="img" aria-label="命势时间序列：实心点为已有记录，空心点为未来推演；空白窗口不连线补值">
      <line x1="20" y1="120" x2="580" y2="120" className="trend-zero"/><path d={path} className="trend-line"/>
      {points.map((value,index) => <g key={value.bucket_id} tabIndex={0} aria-label={`${value.start}至${value.end}，${SEGMENT[value.segment]}，${value.auspice.label}`}><line x1={x(index)} x2={x(index)} y1={y(value.candle!.high)} y2={y(value.candle!.low)} className="trend-wick"/><circle cx={x(index)} cy={y(value.candle!.close)} r="5" className={value.segment === "projected_future" ? "trend-future" : "trend-point"}/></g>)}
    </svg>
    <figcaption>有证契的窗口才形成势位；未来使用空心点。命势长图不是证券价格，也不是单一吉凶曲线。</figcaption>
  </figure>;
}

export default function LifeTrendResearch() {
  const [profile,setProfile] = useState(""); const [evidence,setEvidence] = useState<Evidence[]>([]); const [run,setRun] = useState<Run>();
  const [granularity,setGranularity] = useState("auto"); const [state,setState] = useState("loading"); const [error,setError] = useState("");
  useEffect(() => { const id = readProductSession().subject?.id || ""; setProfile(id); if (!id) { setState("ready"); return; } apiRequest<{factors:Evidence[]}>(`/api/v1/profiles/${id}/life-trend/evidence`).then((value) => { setEvidence(value.factors); setState("ready"); }).catch((cause) => { setError(cause instanceof Error ? cause.message : "读取失败"); setState("error"); }); }, []);
  async function start() { if (state === "running") return; setState("running"); setError(""); try { setRun(await apiRequest<Run>(`/api/v1/profiles/${profile}/life-trend/executions`, {method:"POST",body:JSON.stringify({granularity,future_bucket_count:2,title:"命势长图与三际断章"})})); setState("ready"); } catch (cause) { setError(cause instanceof Error ? cause.message : "执行失败"); setState("error"); } }
  if (state === "loading") return <ProductShell title="命势长图" eyebrow="合参 · 三际断章"><PageState kind="loading" title="正在读取授权资料"><p>正在取证。私人正文不会发送给外部模型。</p></PageState></ProductShell>;
  return <ProductShell title="三际断章与命势长图" eyebrow="合参 · 主报告" status="research only">
    <aside className="privacy-note"><b>三际观原创研究 · 未经审校</b><p>命势长图呈现不同生命主题在各阶段的相对起伏，不代表金融收益，也不是现实准确率声明。往际事实、当下与未来推演会明确分区。</p></aside>
    {!profile ? <PageState kind="insufficient" title="先建立三际录"><p>建立主体并记录带时间精度的事实后，才能起一卷命势观察。</p><Link className="product-button" href="/onboarding">开始立卷</Link></PageState> : <section className="product-form"><h2>准备本次观察</h2><p>{evidence.length} 项结构事实与授权记录可用；资料覆盖只影响证契完备度，不会直接抬高势位。</p><label><span>时间粒度</span><select value={granularity} onChange={(event) => setGranularity(event.target.value)}><option value="auto">按资料精度自动选择</option><option value="month">月</option><option value="quarter">季</option><option value="year">年</option><option value="phase">多年阶段</option></select></label><button className="product-button" aria-disabled={state === "running"} aria-busy={state === "running"} onClick={start}>{state === "running" ? "正在取证、合参与成断…" : "生成命势长图与三际断章"}</button></section>}
    {error && <PageState kind="error" title="本次起卷未完成"><p>{error} 已有三际录未被覆盖，可检查连接后重试。</p></PageState>}
    {run && <>
      <article className="report-reader" aria-labelledby="report-title">
        <div className="report-folio"><span>三际断章</span><b>卷一</b><small>确定性报告</small></div>
        <VerdictBanner status={run.status} title={run.report.chapter}><p>{run.report.plain_interpretation}</p></VerdictBanner>
        <header className="report-masthead"><div><span className="report-kicker">象名</span><h2 className="report-title" id="report-title">{run.report.symbolic_title}</h2></div><dl><div><dt>吉凶主次</dt><dd>{run.report.auspice}</dd></div><div><dt>成文方式</dt><dd>三际枢确定性模板</dd></div></dl></header>
        <div className="report-reading-layout"><nav className="report-index" aria-label="断章目录"><b>本卷目录</b><a href="#report-image">01 象辞</a><a href="#report-plain">02 释义</a><a href="#report-past">03 往际</a><a href="#report-current">04 当下</a><a href="#report-future">05 未来</a><a href="#report-timing">06 应期</a></nav><div className="report-chapters">
          <section className="report-chapter report-chapter--image" id="report-image"><span>01</span><div><h3>象辞</h3><p>{run.report.image_text}</p></div></section><section className="report-chapter" id="report-plain"><span>02</span><div><h3>现代释义</h3><p>{run.report.plain_interpretation}</p></div></section>
          <section className="report-chapter" id="report-past"><span>03</span><div><h3>往际</h3><p>{run.report.past}</p></div></section><section className="report-chapter" id="report-current"><span>04</span><div><h3>当下</h3><p>{run.report.current}</p></div></section><section className="report-chapter" id="report-future"><span>05</span><div><h3>未来</h3><p>{run.report.future}</p></div></section>
          <section className="report-chapter"><span>吉</span><div><h3>吉凶主次</h3><p>{run.report.auspice}</p></div></section>
          <section className="report-chapter" id="report-timing"><span>期</span><div><h3>应期</h3>{run.timing_windows.length ? run.timing_windows.map((window) => <p key={window.window_id}>{window.start}—{window.end} · {WINDOW_LABELS[window.type] || "变化窗口"} · 证契完备度 {window.confidence_bp/100}%</p>) : <p>证契未足，不强造应期。</p>}</div></section>
          <section className="report-chapter"><span>行</span><div><h3>行动提示</h3><p>{run.report.action_guidance}</p></div></section>
        </div></div>
        <footer className="report-footer"><p className="report-provenance">本页使用三际枢确定性模板成文。成文服务未启用时，结构结果与完整报告仍然可读。</p><Link className="product-button" href={`/chronicle/${run.archive_id}`}>收入三际录</Link></footer>
        <TechnicalDetails><dl className="technical-grid"><div><dt>Core Output Hash</dt><dd><code>{run.core_output_hash}</code></dd></div><div><dt>Report Hash</dt><dd><code>{run.deterministic_report_hash}</code></dd></div><div><dt>Trace Hash</dt><dd><code>{run.trace_hash}</code></dd></div><div><dt>状态原值</dt><dd>{productStatus(run.status)}</dd></div></dl></TechnicalDetails>
      </article>
      <section className="chronicle-detail" aria-labelledby="trend-title"><header><span>{productStatus(run.status)}</span><h2 id="trend-title">命势长图</h2><p>历史、当下、未来和资料留白分开呈现；空白时段不会被补成连续曲线。</p></header>
        <Trend values={run.timeline}/>
        <div className="table-scroll"><table><caption>命势长图文字表格回退</caption><thead><tr><th>窗口</th><th>性质</th><th>开 / 高 / 低 / 收</th><th>证契完备度</th><th>资料覆盖</th><th>吉凶</th></tr></thead><tbody>{run.timeline.map((value) => <tr key={value.bucket_id}><th>{value.start}—{value.end}</th><td>{SEGMENT[value.segment]}</td><td>{value.candle ? `${value.candle.open/100} / ${value.candle.high/100} / ${value.candle.low/100} / ${value.candle.close/100}` : "留白"}</td><td>{value.confidence_bp/100}%</td><td>{value.coverage_bp/100}%</td><td>{value.auspice.label}</td></tr>)}</tbody></table></div>
        <div className="mobile-buckets" aria-label="命势长图移动端文字列表">{run.timeline.map((value) => <article key={value.bucket_id}><h3>{value.start}—{value.end}</h3><p>{SEGMENT[value.segment]} · {value.auspice.label}</p><dl><div><dt>开 / 高 / 低 / 收</dt><dd>{value.candle ? `${value.candle.open/100} / ${value.candle.high/100} / ${value.candle.low/100} / ${value.candle.close/100}` : "留白"}</dd></div><div><dt>证契完备度 / 覆盖</dt><dd>{value.confidence_bp/100}% / {value.coverage_bp/100}%</dd></div></dl></article>)}</div>
      </section>
    </>}
  </ProductShell>;
}
