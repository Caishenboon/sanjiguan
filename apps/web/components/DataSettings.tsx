"use client";

import { useEffect, useRef, useState } from "react";
import ProductShell from "./ProductShell";

export default function DataSettings() {
  const [status, setStatus] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [confirming, setConfirming] = useState(false);
  const dialogRef = useRef<HTMLElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const deleteTriggerRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!confirming) return;
    cancelRef.current?.focus();
    function handleDialogKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setConfirming(false);
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const controls = [...dialogRef.current.querySelectorAll<HTMLElement>("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])")];
      if (!controls.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", handleDialogKey);
    return () => { document.removeEventListener("keydown", handleDialogKey); deleteTriggerRef.current?.focus(); };
  }, [confirming]);
  async function download() {
    setStatus("正在生成导出…");
    const response = await fetch("/api/v1/exports", {
      method: "POST",
      credentials: "include",
      headers: { "Idempotency-Key": crypto.randomUUID() },
    });
    if (!response.ok) return setStatus("导出未完成，请稍后重试。");
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = "sanjiguan-export.zip";
    link.click();
    URL.revokeObjectURL(url);
    setStatus("导出已下载。临时导出可立即撤销，服务端最长保留 24 小时。");
  }
  async function removeAccount() {
    if (confirmation !== "DELETE MY SANJIGUAN DATA") {
      return setStatus("请输入完整确认短语。");
    }
    const response = await fetch("/api/v1/account", {
      method: "DELETE",
      credentials: "include",
      headers: {
        "Idempotency-Key": crypto.randomUUID(),
        "X-Delete-Confirmation": confirmation,
      },
    });
    setStatus(response.ok ? "账号和私人派生数据已删除。" : "删除未完成，请检查会话后重试。");
    if (response.ok) setConfirming(false);
  }
  return (
    <ProductShell title="隐私、导出与删除" eyebrow="我的">
      <section className="settings-grid">
        <article>
          <h2>导出个人资料</h2>
          <p>下载规范化资料档案和可阅读报告；方法版本与校验摘要会随归档保存。打印页面可另存为 PDF。</p>
          <button className="product-button" onClick={download}>生成并下载导出</button>
        </article>
        <article>
          <h2>删除说明</h2>
          <p>撤销只影响新的分析；彻底删除可能令历史复演不可用。离线备份会按既定保留周期过期。</p>
        </article>
      </section>
      <section className="product-form" aria-labelledby="delete-account-title">
        <h2 id="delete-account-title">彻底删除账号</h2>
        <label htmlFor="delete-confirmation">输入 DELETE MY SANJIGUAN DATA</label>
        <input id="delete-confirmation" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
        <button ref={deleteTriggerRef} className="danger-button" onClick={()=>setConfirming(true)}>删除账号及私人数据</button>
      </section>
      {confirming&&<div className="dialog-backdrop"><section ref={dialogRef} className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-delete-title"><p className="eyebrow">不可逆操作</p><h2 id="confirm-delete-title">确认彻底删除？</h2><p>账号、主体及私人派生数据将被删除。相关历史可能无法复演；离线备份仍按保留周期处理。</p><div className="form-actions"><button ref={cancelRef} className="secondary-button" onClick={()=>setConfirming(false)}>返回检查</button><button className="danger-button" onClick={removeAccount}>确认彻底删除</button></div></section></div>}
      <p aria-live="polite">{status}</p>
    </ProductShell>
  );
}
