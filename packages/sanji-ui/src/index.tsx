"use client";

import type { PropsWithChildren, ReactNode } from "react";
import { AlertTriangle, CheckCircle2, CircleSlash2, ShieldCheck } from "lucide-react";

export function SanjiShell({ children }: PropsWithChildren) {
  return <div className="sanji-shell">{children}</div>;
}
export function SanjiHeader() {
  return <header className="sanji-header"><a className="sanji-brand" href="/">三际观</a><small>大屏观三际，小屏录一念。</small><ResearchNavigation /></header>;
}
export function ResearchNavigation() {
  return <nav className="sanji-nav" aria-label="研究导航"><a href="/admin/research">总览</a><a href="/admin/research/three-coin">三钱</a><a href="/admin/research/bazi-methods">八字</a><a href="/admin/research/ziwei">紫微</a><a href="/admin/research/oracles">Oracle</a></nav>;
}
export function VerdictStatusBadge({ status }: { status: "decisive"|"provisional"|"contested"|"insufficient" }) {
  const text = {decisive:"成断",provisional:"待验",contested:"两象相争",insufficient:"不成断"}[status];
  return <span className={`sanji-badge sanji-badge--${status==="decisive"?"gold":status==="insufficient"?"risk":"violet"}`}>{text}</span>;
}
export function RulesetBadge({ children="research_active" }: PropsWithChildren) { return <span className="sanji-badge sanji-badge--jade"><ShieldCheck size={13}/>{children}</span>; }
export function ProfileBadge({ children }: PropsWithChildren) { return <span className="sanji-badge sanji-badge--violet">{children}</span>; }
export function EvidenceCard({ title, children }: PropsWithChildren<{title:string}>) { return <article className="sanji-card"><CheckCircle2 color="var(--sanji-jade)" size={18}/><h3>{title}</h3><div>{children}</div></article>; }
export function CounterEvidenceCard({ title, children }: PropsWithChildren<{title:string}>) { return <article className="sanji-card sanji-card--counter"><AlertTriangle color="var(--sanji-risk)" size={18}/><h3>{title}</h3><div>{children}</div></article>; }
export function TraceStep({ index, title, children }: PropsWithChildren<{index:number;title:string}>) { return <div className="sanji-trace"><strong>{String(index).padStart(2,"0")}</strong><div><b>{title}</b><div>{children}</div></div></div>; }
export function HashPanel({ label, value }: {label:string;value:string}) { return <section><small>{label}</small><div className="sanji-hash">{value}</div></section>; }
export function VersionPanel({ items }: {items:Record<string,string>}) { return <section className="sanji-card">{Object.entries(items).map(([k,v])=><HashPanel key={k} label={k} value={v}/>)}</section>; }
export function EmptyState({ title="尚无记录", children }: PropsWithChildren<{title?:string}>) { return <div className="sanji-empty"><CircleSlash2 size={24}/><h3>{title}</h3>{children}</div>; }
export function ErrorState({ title="无法载入", children }: PropsWithChildren<{title?:string}>) { return <div role="alert" className="sanji-empty sanji-error"><AlertTriangle size={24}/><h3>{title}</h3>{children}</div>; }
export function YijingHexagram({ lines=[8,7,8,7,8,7], label="虚构卦例" }: {lines?:number[];label?:string}) { return <figure><div className="sanji-hex" role="img" aria-label={`${label}，六爻自下而上`} >{[...lines].reverse().map((x,i)=><span key={i} className={`sanji-hex-line ${x%2===0?"sanji-hex-line--broken":""}`}/>)}</div><figcaption>{label}</figcaption></figure>; }
export function BaziFourPillars({ pillars=["庚辰","戊寅","癸巳","壬子"] }: {pillars?:string[]}) { return <div className="sanji-pillars" role="img" aria-label={`四柱：${pillars.join("、")}`}>{pillars.map((p,i)=><div className="sanji-pillar" key={i}><small>{["年","月","日","时"][i]}柱</small><b>{p}</b></div>)}</div>; }
export type Palace = { name:string; branch:string; stars?:string[]; body?:boolean };
export function ZiweiPalaceGrid({ palaces }: {palaces:Palace[]}) { return <div className="sanji-palaces" role="img" aria-label="紫微十二宫机械排盘">{palaces.map((p)=><div className="sanji-palace" key={p.name}><b>{p.name}{p.body?" · 身":""}</b><small> {p.branch}</small><span>{p.stars?.join(" · ")||"—"}</span></div>)}</div>; }
export function OracleDiffPanel({ engine, oracle, status }: {engine:ReactNode;oracle:ReactNode;status:string}) { return <section className="sanji-oracle"><div className="sanji-card">{engine}</div><span className="sanji-badge sanji-badge--gold">{status}</span><div className="sanji-card">{oracle}</div></section>; }
export function ResearchWarning({ children }: PropsWithChildren) { return <aside className="sanji-warning"><AlertTriangle size={16}/> {children}</aside>; }
export function ConsentPanel({ checked=false }: {checked?:boolean}) { return <label className="sanji-consent"><input type="checkbox" defaultChecked={checked}/><span>我确认此处仅使用虚构或经明确批准的研究输入；Oracle 结果不改变三际枢输出。</span></label>; }
