"use client";

import Link from "next/link";
import ProductShell from "./ProductShell";

const TOOLS = [
  { id:"yijing", glyph:"易", title:"易经三钱", kind:"机械排盘", status:"可用", needs:"一个正式占问、六次实物三钱结果", description:"按已冻结的币面映射形成本卦、变卦与动爻，不生成卦义评分。", href:"/consult/yijing" },
  { id:"bazi", glyph:"八", title:"八字", kind:"机械排盘", status:"研究可用", needs:"出生日期、地点、历史时区；时刻可标记未知", description:"展示四柱候选、方法方案与边界敏感，不把机械结构包装成完整论命。", href:"/consult/bazi" },
  { id:"ziwei", glyph:"紫", title:"紫微", kind:"机械结构", status:"研究可用", needs:"经确认的出生资料与已批准方法方案", description:"展示命宫、身宫与已实现机械结构，不补充未经审校的星曜断语。", href:"/consult/ziwei" },
  { id:"liuxiang", glyph:"象", title:"六象合参", kind:"真实证据研究", status:"研究可用", needs:"多类授权记录；资料不足也可以如实起卷", description:"以命、业、愿、梦、缘、世六类证契并观；同源去重，保留逆证、冲突与缺失。", href:"/consult/liuxiang" },
  { id:"sushe", glyph:"宿", title:"宿世星图", kind:"原创专题研究", status:"研究可用", needs:"已授权的主体记录与结构标签", description:"排列确定性研究候选；姓名、年代、地点、身份与死因均明确标注为可能。", href:"/consult/sushe" },
  { id:"zhongyin", glyph:"门", title:"中阴之门", kind:"原创专题研究", status:"研究可用", needs:"人生过渡记录；离世模式另需明确离世事实", description:"观察旧结构消散与新结构形成之间的过渡，不预测在世主体的死亡。", href:"/consult/zhongyin" },
  { id:"yuanqi", glyph:"缘", title:"缘契图", kind:"原创专题研究", status:"研究可用", needs:"关系事件、承诺与相应同意范围", description:"区分单方观察与双方合参，不输出命定伴侣或必然复合。", href:"/consult/yuanqi" },
  { id:"life-trend", glyph:"势", title:"三际断章与命势", kind:"原创时序研究", status:"研究可用", needs:"已授权的人生事件、行为、愿向与关系记录", description:"将往际、当下和未来推演分区呈现；空白处不插值，命势长图不是证券价格。", href:"/consult/life-trend" },
] as const;

export default function ConsultCenter(){
  return <ProductShell title="选择一次合参" eyebrow="合参 · 察诸象">
    <header className="consult-masthead"><div><p className="product-kicker">OBSERVATION WORKSPACE</p><h2>诸象不是八个孤立工具，<br/>而是同一卷资料的不同观察面。</h2><p>机械排盘负责形成结构，证据合参负责保留支持与逆证。每项能力都明确标注资料要求和研究边界。</p></div><div className="consult-seal" aria-hidden="true"><span>三际</span><b>合参</b></div></header>
    <section className="consult-section" aria-labelledby="mechanical-title"><header><span>01</span><div><p className="eyebrow">机械结构</p><h2 id="mechanical-title">先立其形</h2></div><p>可复现的盘面与结构，不自动等于人生解释。</p></header><div className="tool-grid tool-grid--mechanical">
      {TOOLS.slice(0,3).map((tool)=><article key={tool.id}><span className="tool-glyph" aria-hidden="true">{tool.glyph}</span><div className="tool-head"><span>{tool.kind}</span><b className="status-ok">{tool.status}</b></div><h2>{tool.title}</h2><p>{tool.description}</p><dl><dt>所需资料</dt><dd>{tool.needs}</dd></dl><Link href={tool.href} aria-label={tool.id === "yijing" ? "开始" : `进入${tool.title}`}>进入观察 <span aria-hidden="true">→</span></Link></article>)}
    </div></section>
    <section className="consult-section" aria-labelledby="synthesis-title"><header><span>02</span><div><p className="eyebrow">证据与专题</p><h2 id="synthesis-title">再察其间</h2></div><p>从已授权记录中取证，资料不足时允许不成断。</p></header><div className="tool-grid tool-grid--synthesis">
      {TOOLS.slice(3).map((tool,index)=><article className={index===0||tool.id==="life-trend"?"tool-featured":""} key={tool.id}><span className="tool-glyph" aria-hidden="true">{tool.glyph}</span><div className="tool-head"><span>{tool.kind}</span><b className="status-ok">{tool.status}</b></div><h2>{tool.title}</h2><p>{tool.description}</p><dl><dt>所需资料</dt><dd>{tool.needs}</dd></dl><Link href={tool.href}>{tool.id==="liuxiang"?"查看资料并合参":"进入专题"} <span aria-hidden="true">→</span></Link></article>)}
    </div></section>
    <p className="research-disclaimer">引擎、规则版本与校验摘要不会占据普通阅读区；需要核验时，可在结果页的“方法与版本”中展开。</p>
  </ProductShell>;
}
