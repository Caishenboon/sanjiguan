"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ProductShell, { PageState } from "./ProductShell";
import { ChronicleSummary, readProductSession } from "../lib/product-session";
export default function ChronicleList(){
 const [items,setItems]=useState<ChronicleSummary[]>([]);const [subject,setSubject]=useState("");const [type,setType]=useState("");const [status,setStatus]=useState("");const [query,setQuery]=useState("");
 useEffect(()=>{const session=readProductSession();setItems(session.chronicles);setSubject(session.subject?.name||"")},[]);
 const shown=useMemo(()=>items.filter(item=>(!type||item.type===type)&&(!status||item.status===status)&&(!query||item.date.includes(query))),[items,type,status,query]);
 return <ProductShell title="我的三际录" eyebrow="三际录 · 历史档案">
  <section className="filter-bar" aria-label="筛选三际录"><label>主体<select value={subject} onChange={(e)=>setSubject(e.target.value)}><option value={subject}>{subject||"当前主体"}</option></select></label><label>类型<select value={type} onChange={(e)=>setType(e.target.value)}><option value="">全部类型</option>{["记录","易经","八字","紫微","六象研究"].map(v=><option key={v}>{v}</option>)}</select></label><label>日期<input type="search" value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="YYYY-MM-DD"/></label><label>状态<select value={status} onChange={(e)=>setStatus(e.target.value)}><option value="">全部状态</option>{Array.from(new Set(items.map(v=>v.status))).map(v=><option key={v}>{v}</option>)}</select></label></section>
  {!items.length?<PageState kind="empty" title="三际录还是空的"><p>保存一条记录或完成一次机械工具后，它会按时间出现在这里。</p><Link className="product-button" href="/records">记录第一件事</Link></PageState>:
  !shown.length?<PageState kind="empty" title="没有符合条件的记录"><p>尝试清除筛选条件。</p><button className="secondary-button" onClick={()=>{setType("");setStatus("");setQuery("")}}>清除筛选</button></PageState>:
  <section className="chronicle-list" aria-label="三际录列表">{shown.map(item=><Link href={`/chronicle/${item.id}`} key={item.id}><time>{item.date}</time><div><small>{item.subject} · {item.type}</small><h2>{item.title}</h2><p>{item.source}</p></div><span><b>{item.status}</b><small>{item.replayable?"可按原版本重放":"原始记录"}</small></span></Link>)}</section>}
 </ProductShell>
}
