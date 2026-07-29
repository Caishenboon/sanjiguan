"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState, TechnicalDetails } from "./ProductShell";
import { ChronicleSummary, readProductSession } from "../lib/product-session";
export default function ChronicleDetail({recordId}:{recordId:string}){
 const [item,setItem]=useState<ChronicleSummary>();const [ready,setReady]=useState(false);
 useEffect(()=>{setItem(readProductSession().chronicles.find(v=>v.id===recordId));setReady(true)},[recordId]);
 if(!ready)return <ProductShell title="读取三际录" eyebrow="三际录"><PageState kind="loading" title="正在读取记录"><p>正在核对当前会话引用。</p></PageState></ProductShell>
 if(!item)return <ProductShell title="记录不可用" eyebrow="三际录"><PageState kind="withdrawn" title="记录已撤销或当前无权查看"><p>这里不会显示原始异常或已撤销正文。</p><Link className="product-button" href="/chronicle">返回列表</Link></PageState></ProductShell>
 return <ProductShell title={item.title} eyebrow="三际录 · 记录详情">
  <article className="chronicle-detail"><header><time>{item.date}</time><span>{item.status}</span><h2>{item.subject} · {item.type}</h2></header>
   <section><span>01</span><div><h2>当时记录了什么</h2><p>为保护敏感资料，当前会话摘要不复制保存正文；登录后从加密服务端读取原始内容。</p></div></section>
   <section><span>02</span><div><h2>当时执行了什么</h2><p>{item.type==="易经"?"按实物三钱方法形成机械结构。":"保存了一条原始记录，没有自动执行术数分析。"}</p></div></section>
   <section><span>03</span><div><h2>当时得到什么结果</h2><p>{item.status}。没有生成最终吉凶、应期或宿世身份。</p>{item.type==="易经"&&<Link href={`/results/${item.id}`}>阅读机械结果</Link>}</div></section>
   <section><span>04</span><div><h2>使用了哪些资料</h2><p>记录来源：{item.source}。主体：{item.subject}。</p></div></section>
   <section><span>05</span><div><h2>哪些资料当时缺失</h2><p>服务端记录会保留日期精度、未知项和边界状态；摘要不会把未知补齐。</p></div></section>
  </article>
  <TechnicalDetails><dl className="technical-grid"><div><dt>Record ID</dt><dd><code>{item.id}</code></dd></div><div><dt>原版本回放</dt><dd>{item.replayable?"可按原版本重放":"此类原始记录无需重放"}</dd></div><div><dt>重新分析</dt><dd>用当前版本重新分析尚未开放；不会显示虚假按钮。</dd></div></dl></TechnicalDetails>
 </ProductShell>
}
