"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell from "./ProductShell";
import { apiRequest } from "../lib/product-session";

export default function MeSettings() {
  const [canResearch, setCanResearch] = useState(false);
  const [invitation, setInvitation] = useState<{token:string;role:string;expires_at:string}|null>(null);
  const [inviteError, setInviteError] = useState("");
  async function issueInvitation(role: "member" | "viewer") {
    setInviteError("");
    try { setInvitation(await apiRequest("/api/v1/auth/invitations", {method:"POST", body:JSON.stringify({role,expires_hours:24})})); }
    catch (error) { setInviteError(error instanceof Error ? error.message : "邀请未生成"); }
  }
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    apiRequest<{role:string}>("/api/v1/me", { signal: controller.signal })
      .then((body) => { if (active) setCanResearch(body.role === "owner" || body.role === "research_admin"); })
      .catch(() => {});
    return () => { active = false; controller.abort(); };
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
        <><section className="research-admin-entry">
          <div>
            <p className="eyebrow">仅授权角色可见</p>
            <h2>研究与管理</h2>
            <p>六象研究、数据源、Signal、Mapping、Trace 与质量报告位于独立后台。</p>
          </div>
          <Link className="product-button" href="/admin/research">进入研究后台</Link>
        </section><section className="scope-card"><h2>签发一次性邀请</h2><p>令牌只在这里显示一次，数据库仅保存哈希；24小时后失效。</p><div className="button-row"><button className="product-button" onClick={()=>issueInvitation("member")}>邀请 Member</button><button className="quiet-button" onClick={()=>issueInvitation("viewer")}>邀请 Viewer</button></div>{invitation&&<div className="technical-details"><p><b>{invitation.role}</b> · 有效至 {invitation.expires_at}</p><code className="break-anywhere">{invitation.token}</code><p>请通过安全渠道交给受邀者，不要写入聊天、文档或日志。</p></div>}{inviteError&&<p role="alert" className="field-error">{inviteError}</p>}</section></>
      )}
      {!canResearch && (
        <p className="boundary">当前是普通用户空间。研究后台不会出现在主导航中，也不能由普通会话直接访问。</p>
      )}
    </ProductShell>
  );
}
