"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell from "./ProductShell";
import { ProductSession, readProductSession } from "../lib/product-session";

const TOOLS = [
  { id:"yijing", title:"易经三钱", kind:"机械排盘", status:"可用", needs:"一个正式占问、六次实物三钱结果", description:"按已冻结的币面映射形成本卦、变卦与动爻，不生成卦义评分。", href:"/consult/yijing" },
  { id:"bazi", title:"八字", kind:"机械排盘", status:"研究可用", needs:"出生日期、地点、历史时区；时刻可标记未知", description:"展示四柱候选、Profile 与边界敏感，不判断旺衰、喜忌或大运。", href:"/consult/bazi" },
  { id:"ziwei", title:"紫微", kind:"机械结构", status:"研究可用", needs:"经确认的出生资料与已批准方法 Profile", description:"展示命宫、身宫与已实现机械结构，不补充未经审校的星曜断语。", href:"/consult/ziwei" },
  { id:"liuxiang", title:"六象研究", kind:"研究框架", status:"暂不成断", needs:"多类长期资料与通过审校的真实映射规则", description:"框架与资料准备度已建立；真实映射尚未启用，普通用户不会看到合成测试候选。", href:"/consult/liuxiang" },
] as const;

export default function ConsultCenter(){
  const [session,setSession]=useState<ProductSession>({chronicles:[]});
  useEffect(()=>setSession(readProductSession()),[]);
  return <ProductShell title="选择一次合参" eyebrow="合参 · 察诸象">
    <header className="section-intro"><div><h2>先看当前能力，再决定是否开始</h2><p>每项工具都会标明资料要求、机械或研究性质，以及尚未开放的结论范围。</p></div></header>
    <section className="tool-grid">
      {TOOLS.map((tool)=><article key={tool.id}><div className="tool-head"><span>{tool.kind}</span><b className={tool.status==="暂不成断"?"status-risk":"status-ok"}>{tool.status}</b></div><h2>{tool.title}</h2><p>{tool.description}</p><dl><dt>需要资料</dt><dd>{tool.needs}</dd><dt>最近一次</dt><dd>{session.recentRun?.tool===tool.id?session.recentRun.completedAt:"尚未执行"}</dd></dl><Link className="product-button" href={tool.href}>{tool.id==="liuxiang"?"查看准备度":tool.status==="可用"?"开始":"查看机械范围"}</Link></article>)}
    </section>
    <p className="research-disclaimer">这里不会展示 Engine、Hash 或 Dataset Revision；这些信息只在结果页的“研究详情”中按需展开。</p>
  </ProductShell>;
}
