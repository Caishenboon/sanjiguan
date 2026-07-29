"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState } from "./ProductShell";
import { ProductSession, readProductSession } from "../lib/product-session";

export const RECORD_TYPES = [
  { id: "dream", title: "梦境", time: "2–4 分钟", use: "保留梦中原貌与醒后记忆", privacy: "只涉及本人时可直接记录", icon: "梦" },
  { id: "vow_action", title: "愿向或目标", time: "2–3 分钟", use: "追踪愿向与已经采取的行动", privacy: "可随时撤回", icon: "愿" },
  { id: "life_event", title: "人生事件", time: "2–5 分钟", use: "建立有日期精度的事实时间线", privacy: "允许日期不确定", icon: "事" },
  { id: "reflection", title: "行为或日记", time: "1–3 分钟", use: "保存当下观察，不自动推断", privacy: "可保存草稿", icon: "记" },
  { id: "relationship", title: "关系事件", time: "3–5 分钟", use: "记录事件与同意边界", privacy: "涉及他人，请匿名或取得同意", icon: "缘" },
  { id: "three_coin", title: "易经三钱记录", time: "4–8 分钟", use: "录入正式占问的六次实物投掷", privacy: "不由系统随机起卦", icon: "卦" },
] as const;

export default function RecordCenter() {
  const [session, setSession] = useState<ProductSession>({ chronicles: [] });
  useEffect(() => setSession(readProductSession()), []);
  return <ProductShell title="这次想记录什么？" eyebrow="记录 · 录一念">
    {!session.subject && <PageState kind="insufficient" title="先选择或建立主体"><p>记录需要归入一个主体档案。建立资料后会回到这里。</p><Link className="product-button" href="/onboarding">建立主体</Link></PageState>}
    <section className="record-grid" aria-label="记录类型">
      {RECORD_TYPES.map((item) => <article key={item.id}>
        <span className="record-glyph" aria-hidden="true">{item.icon}</span><div><h2>{item.title}</h2><p>{item.use}</p>
        <dl><div><dt>大约需要</dt><dd>{item.time}</dd></div><div><dt>隐私与撤回</dt><dd>{item.privacy}</dd></div></dl>
        <Link aria-disabled={!session.subject} className={!session.subject ? "product-button is-disabled" : "product-button"} href={session.subject ? (item.id === "three_coin" ? "/consult/yijing" : `/records/new?type=${item.id}`) : "/onboarding"}>开始记录</Link></div>
      </article>)}
    </section>
    <aside className="privacy-note"><b>如实记录原则</b><p>不知道的日期、时刻或细节可以选择“不确定”。系统不会为了完成表单而补造信息。</p></aside>
  </ProductShell>;
}
