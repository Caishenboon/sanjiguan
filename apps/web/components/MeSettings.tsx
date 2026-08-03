"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell from "./ProductShell";

export default function MeSettings() {
  const [canResearch, setCanResearch] = useState(false);
  useEffect(() => {
    let active = true;
    fetch("/api/v1/me", { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) return;
        const body = await response.json();
        if (active) setCanResearch(body.role === "owner" || body.role === "research_admin");
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);
  return (
    <ProductShell title="我的主体与设置" eyebrow="我的">
      <section className="settings-grid">
        <article>
          <h2>主体资料</h2>
          <p>查看称呼、出生原始记录、时间精度和用户确认状态。</p>
          <Link className="product-button" href="/onboarding">查看或完善</Link>
        </article>
        <article>
          <h2>隐私、导出与删除</h2>
          <p>主动导出个人资料，或管理撤销、彻底删除与账号删除。</p>
          <Link className="product-button" href="/me/data">管理我的资料</Link>
        </article>
        <article>
          <h2>版本与回放</h2>
          <p>原结果按原版本保存；重新分析会另建执行，不覆盖历史。</p>
          <Link href="/chronicle">查看三际录</Link>
        </article>
      </section>
      {canResearch && (
        <section className="research-admin-entry">
          <div>
            <p className="eyebrow">仅授权角色可见</p>
            <h2>研究与管理</h2>
            <p>六象研究、数据源、Signal、Mapping、Trace 与质量报告位于独立后台。</p>
          </div>
          <Link className="product-button" href="/admin/research">进入研究后台</Link>
        </section>
      )}
      {!canResearch && (
        <p className="boundary">当前是普通用户空间。研究后台不会出现在主导航中，也不能由普通会话直接访问。</p>
      )}
    </ProductShell>
  );
}
