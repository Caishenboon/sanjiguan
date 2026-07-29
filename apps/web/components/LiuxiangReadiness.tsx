"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState } from "./ProductShell";
import { ProductSession, readProductSession } from "../lib/product-session";
const needs=[["出生与机械结构","出生资料、时间精度和边界状态"],["梦境记录","重复梦象与可观察的现实反证"],["愿向与行动","愿心、承诺与已经采取的行动"],["人生事件","有日期精度的重要事件"],["关系事件","匿名或具备同意记录的关系事实"],["长期观照","行为、感受与变化的连续记录"]];
export default function LiuxiangReadiness(){
 const [session,setSession]=useState<ProductSession>({chronicles:[]});useEffect(()=>setSession(readProductSession()),[]);
 return <ProductShell title="六象资料准备度" eyebrow="合参 · 六象研究" status="research only">
  <PageState kind="disabled" title="资料不足，暂不成断"><p>六象框架已经建立，但易经、八字、紫微到六象的真实映射规则尚未通过审校，因此不会生成候选、分数或结论。</p></PageState>
  <section className="readiness-list"><div className="product-section-head"><div><h2>可以继续准备的资料</h2><p>这里显示资料类型，不显示任何合成测试结果。</p></div><span>{session.chronicles.length} 条会话记录</span></div>
   {needs.map(([title,desc],index)=><article key={title}><span aria-hidden="true">{String(index+1).padStart(2,"0")}</span><div><h3>{title}</h3><p>{desc}</p></div><b>{index===0&&session.subject?"已有基础资料":"可继续记录"}</b></article>)}
  </section>
  <aside className="privacy-note"><b>为什么暂不成断？</b><p>研究平台的合成一致性案例只能证明软件确定性，不能证明真实人生结论。真实 Mapping 继续保持禁用。</p><Link className="product-button" href="/records">继续记录资料</Link></aside>
 </ProductShell>
}
