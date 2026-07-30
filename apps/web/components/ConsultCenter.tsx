"use client";

import Link from "next/link";
import ProductShell from "./ProductShell";

const TOOLS = [
  { id:"yijing", title:"易经三钱", kind:"机械排盘", status:"可用", needs:"一个正式占问、六次实物三钱结果", description:"按已冻结的币面映射形成本卦、变卦与动爻，不生成卦义评分。", href:"/consult/yijing" },
  { id:"bazi", title:"八字", kind:"机械排盘", status:"研究可用", needs:"出生日期、地点、历史时区；时刻可标记未知", description:"展示四柱候选、Profile 与边界敏感，不判断旺衰、喜忌或大运。", href:"/consult/bazi" },
  { id:"ziwei", title:"紫微", kind:"机械结构", status:"研究可用", needs:"经确认的出生资料与已批准方法 Profile", description:"展示命宫、身宫与已实现机械结构，不补充未经审校的星曜断语。", href:"/consult/ziwei" },
  { id:"liuxiang", title:"六象研究", kind:"真实证据研究", status:"研究可用", needs:"多类授权记录；资料不足也可诚实执行", description:"只用版本化证据政策处理明确记录；传统解释性映射仍禁用，也不会展示合成测试候选。", href:"/consult/liuxiang" },
  { id:"sushe", title:"宿世观", kind:"原创专题研究", status:"研究可用", needs:"已授权的主体记录与结构标签", description:"生成一至三组确定性研究候选；姓名、年代、地点、身份与死因均明确标注为可能，不主张历史事实。", href:"/consult/sushe" },
  { id:"zhongyin", title:"中阴观", kind:"原创专题研究", status:"研究可用", needs:"人生过渡记录；离世模式另需明确离世事实", description:"观察人生结构过渡；不会预测在世主体的死亡时间、死法或寿命。", href:"/consult/zhongyin" },
  { id:"yuanqi", title:"缘契观", kind:"原创专题研究", status:"研究可用", needs:"关系事件、承诺与相应同意范围", description:"区分单方观察与双方合参，不输出命定伴侣、必然复合或不可改变的关系结论。", href:"/consult/yuanqi" },
  { id:"life-trend", title:"命势长图", kind:"原创时序研究", status:"研究可用", needs:"已授权的人生事件、行为、愿向与关系记录", description:"确定性展示往际、当下和规则推演的未来；空白处不插值，K线不是证券价格。", href:"/consult/life-trend" },
] as const;

export default function ConsultCenter(){
  return <ProductShell title="选择一次合参" eyebrow="合参 · 察诸象">
    <header className="section-intro"><div><h2>先看当前能力，再决定是否开始</h2><p>每项工具都会标明资料要求、机械或研究性质，以及尚未开放的结论范围。</p></div></header>
    <section className="tool-grid">
      {TOOLS.map((tool)=><article key={tool.id}><div className="tool-head"><span>{tool.kind}</span><b className="status-ok">{tool.status}</b></div><h2>{tool.title}</h2><p>{tool.description}</p><dl><dt>需要资料</dt><dd>{tool.needs}</dd><dt>最近一次</dt><dd>从服务端历史读取</dd></dl><Link className="product-button" href={tool.href}>{tool.id==="liuxiang"?"查看资料并执行":tool.status==="可用"?"开始":"查看机械范围"}</Link></article>)}
    </section>
    <p className="research-disclaimer">这里不会展示 Engine、Hash 或 Dataset Revision；这些信息只在结果页的“研究详情”中按需展开。</p>
  </ProductShell>;
}
