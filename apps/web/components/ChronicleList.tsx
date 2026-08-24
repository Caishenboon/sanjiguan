"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ProductShell, { PageState } from "./ProductShell";
import { apiRequest, readProductSession } from "../lib/product-session";
type Entry={id:string;profile_id:string;execution_id:string|null;entry_type:string;title:string;status:string;replay_available:boolean;created_at:string;withdrawn:boolean};
const typeName:Record<string,string>={record:"记录",mechanical_result:"机械结果",liuxiang_research:"六象合参",topic_research:"专题推演",life_trend_report:"命势长图与三际断章"};
const statusName:Record<string,string>={decisive:"象成，可断",provisional:"象初成，仍待补证",contested:"两象相争",insufficient:"证契未足，不成断",recorded:"已记录"};
export default function ChronicleList(){
 const [items,setItems]=useState<Entry[]>([]);const [type,setType]=useState("");const [status,setStatus]=useState("");const [query,setQuery]=useState("");const [loading,setLoading]=useState(true);const [error,setError]=useState("");
 useEffect(()=>{const profile=readProductSession().subject?.id;apiRequest<{items:Entry[]}>(`/api/v1/chronicle${profile?`?profile_id=${profile}`:""}`).then(v=>setItems(v.items)).catch(e=>setError(e instanceof Error?e.message:"读取失败")).finally(()=>setLoading(false))},[]);
 const shown=useMemo(()=>items.filter(item=>(!type||item.entry_type===type)&&(!status||item.status===status)&&(!query||item.created_at.slice(0,10).includes(query))),[items,type,status,query]);
 return <ProductShell title="我的三际录" eyebrow="三际录 · 数据库历史档案">
  <section className="filter-bar" aria-label="筛选三际录"><label>类型<select value={type} onChange={e=>setType(e.target.value)}><option value="">全部类型</option>{Object.entries(typeName).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label><label>日期<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="YYYY-MM-DD"/></label><label>状态<select value={status} onChange={e=>setStatus(e.target.value)}><option value="">全部状态</option>{Array.from(new Set(items.map(v=>v.status))).map(v=><option key={v}>{v}</option>)}</select></label></section>
  {loading?<PageState kind="loading" title="正在读取三际录"><p>数据库是唯一事实来源。</p></PageState>:error?<PageState kind="error" title="三际录读取失败"><p>{error}。请检查连接后重试。</p></PageState>:!items.length?<PageState kind="empty" title="三际录还是空的"><p>保存一条记录或完成六象研究后，它会写入加密数据库并出现在这里。</p><Link className="product-button" href="/records">记录第一件事</Link></PageState>:!shown.length?<PageState kind="empty" title="没有符合条件的记录"><button className="secondary-button" onClick={()=>{setType("");setStatus("");setQuery("")}}>清除筛选</button></PageState>:
  <section className="chronicle-list" aria-label="三际录列表">{shown.map(item=><Link href={`/chronicle/${item.id}`} key={item.id}><time>{item.created_at.slice(0,10)}</time><div><small>{typeName[item.entry_type]||item.entry_type}</small><h2>{item.title}</h2><p>{item.withdrawn?"已撤销":"已保存到三际录"}</p></div><span><b>{statusName[item.status]||item.status}</b><small>{item.replay_available?"可复演":"原始记录"}</small></span></Link>)}</section>}
 </ProductShell>
}
