"use client";

import { useState } from "react";
import ProductShell from "./ProductShell";

export default function DataSettings() {
  const [status, setStatus] = useState("");
  const [confirmation, setConfirmation] = useState("");
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
  }
  return (
    <ProductShell title="隐私、导出与删除" eyebrow="我的">
      <section className="settings-grid">
        <article>
          <h2>导出个人资料</h2>
          <p>下载规范化 JSON、可阅读 Markdown、版本与 Hash Manifest。打印页面可另存为 PDF。</p>
          <button className="product-button" onClick={download}>生成并下载导出</button>
        </article>
        <article>
          <h2>删除说明</h2>
          <p>撤销只影响新执行；彻底删除会令相关 Replay 不可用。离线备份按保留周期过期。</p>
        </article>
      </section>
      <section className="product-form" aria-labelledby="delete-account-title">
        <h2 id="delete-account-title">彻底删除账号</h2>
        <label htmlFor="delete-confirmation">输入 DELETE MY SANJIGUAN DATA</label>
        <input id="delete-confirmation" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
        <button className="secondary-button" onClick={removeAccount}>删除账号及私人数据</button>
      </section>
      <p aria-live="polite">{status}</p>
    </ProductShell>
  );
}
