"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { percentFromBasisPoints, productStatus } from "../lib/product-language";

const NAV = [
  { label: "首页", subtitle: "观三际", href: "/" },
  { label: "记录", subtitle: "录一念", href: "/records" },
  { label: "合参", subtitle: "察诸象", href: "/consult" },
  { label: "三际录", subtitle: "阅往迹", href: "/chronicle" },
  { label: "我的", subtitle: "主体与设置", href: "/me" },
] as const;

const MOBILE_NAV = [
  { label: "首页", glyph: "观", href: "/" },
  { label: "三际录", glyph: "卷", href: "/chronicle" },
  { label: "合参", glyph: "象", href: "/consult" },
  { label: "断章", glyph: "章", href: "/consult/life-trend" },
  { label: "更多", glyph: "···", href: "/me" },
] as const;

const STATUS_LABELS: Record<string, string> = {
  "research only": "研究态 · 未经审校",
  research_active: "研究态 · 未经审校",
  "research_active · UNCONFIRMED": "研究态 · 未经审校",
};

export default function ProductShell({
  title,
  eyebrow,
  children,
  status = "个人空间",
}: {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  status?: string;
}) {
  const pathname = usePathname();
  const parent = pathname.startsWith("/consult/") ? { href: "/consult", label: "返回合参" }
    : pathname.startsWith("/chronicle/") ? { href: "/chronicle", label: "返回三际录" }
    : pathname.startsWith("/records/") ? { href: "/records", label: "返回记录" }
    : pathname.startsWith("/me/") ? { href: "/me", label: "返回我的" }
    : pathname.startsWith("/results/") ? { href: "/chronicle", label: "返回三际录" }
    : pathname === "/onboarding" || pathname === "/start" || pathname === "/offline" ? { href: "/", label: "返回首页" }
    : null;
  return (
    <div className="product-shell">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <aside className="product-sidebar">
        <Link href="/" className="product-brand"><i aria-hidden="true">际</i><span><strong>三际观</strong><small>SANJI OBSERVATORY</small></span></Link>
        <p className="product-space-label"><span aria-hidden="true"/>私人研究空间</p>
        <nav aria-label="普通用户主导航">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}>
              <b>{item.label}</b><small>{item.subtitle}</small>
            </Link>;
          })}
        </nav>
        <Link className="sidebar-consult-entry" href="/consult"><span>合参工作区</span><b>进入诸象 →</b><small>八字 · 紫微 · 易经 · 六象 · 专题</small></Link>
        <p className="product-boundary"><b>研究边界</b><span>机械排盘与推演状态如实标注。未审校规则不冒充传统定论。</span></p>
      </aside>
      <div className="product-main">
        <header className="product-topbar">
          <div>{parent && <Link className="breadcrumb-back" href={parent.href}>← {parent.label}</Link>}<p className="eyebrow">{eyebrow || "三际观"}</p><h1>{title}</h1></div>
          <span className="status-dot">{STATUS_LABELS[status] ?? status}</span>
        </header>
        <main id="main-content" className="product-content">{children}</main>
      </div>
      <nav className="product-mobile-nav" aria-label="普通用户手机主导航">
        {MOBILE_NAV.map((item) => <Link key={item.href} href={item.href} aria-current={(item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)) ? "page" : undefined}><span aria-hidden="true">{item.glyph}</span><b>{item.label}</b></Link>)}
      </nav>
    </div>
  );
}

export function PageState({
  kind,
  title,
  children,
  action,
}: {
  kind: "empty" | "loading" | "success" | "error" | "insufficient" | "forbidden" | "withdrawn" | "disabled";
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  const role = kind === "error" ? "alert" : "status";
  return <section className={`product-state product-state--${kind}`} role={role} aria-live="polite">
    <span aria-hidden="true">{({empty:"○",loading:"…",success:"✓",error:"!",insufficient:"△",forbidden:"⊘",withdrawn:"—",disabled:"◇"})[kind]}</span>
    <div><h2>{title}</h2><div>{children}</div>{action && <div className="state-action">{action}</div>}</div>
  </section>;
}

export function TechnicalDetails({ children }: { children: ReactNode }) {
  return <details className="technical-details"><summary>方法与版本</summary><p className="boundary">以下内容用于核验、复演与两卷参照，普通阅读无需理解。</p>{children}</details>;
}

export function MetricPair({ strengthBp, confidenceBp }: { strengthBp: number; confidenceBp: number }) {
  return <div className="metric-pair" aria-label={`象势 ${percentFromBasisPoints(strengthBp)}，证契完备度 ${percentFromBasisPoints(confidenceBp)}`}>
    <div><span>象势</span><strong>{percentFromBasisPoints(strengthBp)}</strong><small>现有证契指向该象的力度</small></div>
    <div><span>证契完备度</span><strong>{percentFromBasisPoints(confidenceBp)}</strong><small>独立资料的完整、稳定与少冲突程度</small></div>
  </div>;
}

export function VerdictBanner({ status, title, children }: { status: string; title?: string; children?: ReactNode }) {
  return <section className={`verdict-banner verdict-banner--${status}`} aria-labelledby="verdict-title">
    <p className="eyebrow">本次断语</p>
    <h2 id="verdict-title">{title ?? productStatus(status)}</h2>
    {children}
  </section>;
}
