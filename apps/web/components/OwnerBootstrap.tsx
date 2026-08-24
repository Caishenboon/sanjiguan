"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import ProductShell from "./ProductShell";
import { apiRequest } from "../lib/product-session";

export default function OwnerBootstrap() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState<"owner" | "invited">("owner");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await apiRequest("/api/v1/auth/bootstrap-owner", {
        method: "POST",
        body: JSON.stringify({ bootstrap_token: token, email }),
      });
      router.push("/onboarding");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "初始化未完成。");
    } finally {
      setSaving(false);
    }
  }
  async function acceptInvitation(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await apiRequest("/api/v1/auth/invitations/accept", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      router.push("/onboarding");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "登录未完成。");
    } finally { setSaving(false); }
  }
  return (
    <ProductShell title="建立本地所有者" eyebrow="首次使用">
      <div className="segmented-control" role="group" aria-label="进入方式">
        <button type="button" aria-pressed={mode === "owner"} onClick={() => {setMode("owner");setError("")}}>首次建立 Owner</button>
        <button type="button" aria-pressed={mode === "invited"} onClick={() => {setMode("invited");setError("")}}>使用邀请进入</button>
      </div>
      <form className="product-form" onSubmit={mode === "owner" ? submit : acceptInvitation}>
        <p className="boundary">三际观 V1 是私人研究工具。研究态推演不等于已经验证的事实。</p>
        {mode === "owner" && <><label htmlFor="owner-email">所有者称谓或邮箱</label><input id="owner-email" value={email} onChange={(event) => setEmail(event.target.value)} /></>}
        <label htmlFor="bootstrap-token">{mode === "owner" ? "一次性初始化口令" : "一次性邀请令牌"}</label>
        <input id="bootstrap-token" type="password" autoComplete="one-time-code" value={token} onChange={(event) => setToken(event.target.value)} required />
        {error && <p className="field-error" role="alert">{error}</p>}
        <button className="product-button" disabled={saving}>{saving ? "正在处理…" : mode === "owner" ? "建立所有者并继续" : "接受邀请并进入"}</button>
      </form>
    </ProductShell>
  );
}
