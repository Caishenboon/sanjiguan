"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState } from "./ProductShell";
import { ProductSession, readProductSession } from "../lib/product-session";

export default function ProductHome() {
  const [session, setSession] = useState<ProductSession>({ chronicles: [] });
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const refresh = () => { setSession(readProductSession()); setReady(true); };
    refresh();
    window.addEventListener("sanjiguan:session-change", refresh);
    return () => window.removeEventListener("sanjiguan:session-change", refresh);
  }, []);

  const latest = session.chronicles[0];
  return <ProductShell title={session.subject ? `欢迎回来，${session.subject.name}` : "从一份如实记录开始"} eyebrow="首页 · 观三际">
    <section className="product-hero">
      <div><p className="product-kicker">过去 · 当下 · 未来</p><h2>先把事实安放好，再察其间的关系。</h2>
      <p>三际观保存原始资料、机械结构和版本边界；未知不会被补造，研究不会被说成定论。</p></div>
      {!ready ? <PageState kind="loading" title="正在读取个人空间"><p>只读取当前安全会话所需的最小摘要。</p></PageState> :
       !session.subject ? <PageState kind="empty" title="还没有主体档案"><p>先建立自己的资料，出生时刻不知道也可以如实选择“未知”。</p></PageState> :
       <PageState kind="success" title="主体资料已建立"><p>{session.subject.name} · 出生时刻精度：{session.subject.timePrecision === "unknown" ? "未知" : "已记录"}</p></PageState>}
    </section>

    <section aria-labelledby="home-actions">
      <div className="product-section-head"><div><p className="eyebrow">现在可以做</p><h2 id="home-actions">选择一个清楚的下一步</h2></div></div>
      <div className="action-grid">
        <Link className="action-card action-card--primary" href="/onboarding"><span>01</span><h3>{session.subject ? "完善我的资料" : "建立我的资料"}</h3><p>约 3 分钟 · 可保留未知项</p><b>继续</b></Link>
        <Link className="action-card" href="/records"><span>02</span><h3>记录一件事</h3><p>约 1–3 分钟 · 随时可撤销</p><b>选择记录类型</b></Link>
        <Link className="action-card" href="/consult"><span>03</span><h3>开始一次合参</h3><p>先查看工具所需资料与当前状态</p><b>查看工具</b></Link>
      </div>
    </section>

    <section className="product-dashboard" aria-labelledby="recent-heading">
      <div className="product-section-head"><div><p className="eyebrow">最近状态</p><h2 id="recent-heading">从上次停下的地方继续</h2></div></div>
      <article><small>最近记录</small><h3>{latest?.title || "尚无记录"}</h3><p>{latest ? `${latest.date} · ${latest.type}` : "写下梦境、愿向、事件或一段观照。"}</p><Link href="/chronicle">打开三际录</Link></article>
      <article><small>最近工具</small><h3>{session.recentRun?.title || "尚未执行"}</h3><p>{session.recentRun ? "机械结果已经保存，可继续阅读。" : "易经、八字与紫微会标注机械或研究边界。"}</p><Link href={session.recentRun ? `/results/${session.recentRun.id}` : "/consult"}>{session.recentRun ? "继续阅读" : "查看合参"}</Link></article>
      <article><small>需要补充</small><h3>{session.subject?.timePrecision === "unknown" ? "出生时刻仍未知" : session.subject ? "可继续记录长期事实" : "主体基本资料"}</h3><p>未知值保持未知，不会自动填成中午、午夜或随机时辰。</p><Link href={session.subject ? "/records" : "/onboarding"}>去补充</Link></article>
    </section>
    {session.pendingTask && <section className="continue-task"><div><small>未完成任务</small><h2>{session.pendingTask.label}</h2></div><Link className="product-button" href={session.pendingTask.href}>继续上次任务</Link></section>}
  </ProductShell>;
}
