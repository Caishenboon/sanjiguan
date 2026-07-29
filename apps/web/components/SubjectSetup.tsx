"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ProductShell, { PageState } from "./ProductShell";
import { apiRequest, readProductSession, updateProductSession } from "../lib/product-session";

type ProfileResponse = { id: string };

export default function SubjectSetup() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [unknownTime, setUnknownTime] = useState(false);
  const [place, setPlace] = useState("");
  const [timezone, setTimezone] = useState("Asia/Shanghai");
  const [confirmed, setConfirmed] = useState(false);
  const [status, setStatus] = useState<"idle"|"saving"|"error">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = readProductSession().subject;
    if (saved) {
      setName(saved.name);
      setBirthDate(saved.birthDate);
      setUnknownTime(saved.timePrecision === "unknown");
    }
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!name.trim() || !birthDate || (!unknownTime && !birthTime) || !place.trim() || !confirmed) {
      setError("请补全必填项；若不知道出生时刻，请选择“出生时刻未知”。");
      return;
    }
    setStatus("saving");
    try {
      const payload = {
        display_name: name.trim(),
        consent_version: "profile-consent/1.0",
        birth: {
          calendar_type: "gregorian",
          local_date: birthDate,
          local_time: unknownTime ? null : `${birthTime}:00`,
          timezone_id: timezone,
          timezone_database: "IANA",
          timezone_database_version: "2025b",
          time_precision: unknownTime ? "unknown" : "minute",
          place: { label: place.trim(), latitude: 0, longitude: 0, coordinate_source: "user_pending_geocode" },
          user_confirmed: confirmed,
          captured_at: new Date().toISOString(),
        },
      };
      const current = readProductSession().subject;
      const updatePayload = { display_name: payload.display_name, birth: payload.birth };
      const response = current
        ? await apiRequest<ProfileResponse>(`/api/v1/profiles/${current.id}`, { method: "PATCH", body: JSON.stringify(updatePayload) })
        : await apiRequest<ProfileResponse>("/api/v1/profiles", { method: "POST", body: JSON.stringify(payload) });
      updateProductSession((session) => ({
        ...session,
        subject: { id: response.id || current?.id || "", name: name.trim(), birthDate, timePrecision: unknownTime ? "unknown" : "minute" },
        pendingTask: { label: "记录第一件重要的事", href: "/records" },
      }));
      router.push("/?welcome=1");
    } catch (cause) {
      setStatus("error");
      setError(cause instanceof Error ? `保存未完成：${cause.message}。请检查网络后重试。` : "保存未完成，请检查网络后重试。");
    }
  }

  return <ProductShell title="建立主体资料" eyebrow="我的 · 基本资料">
    <div className="form-layout">
      <form className="product-form" onSubmit={submit} noValidate>
        <div className="product-section-head"><div><p className="eyebrow">第一步</p><h2>只记录你确认过的原始资料</h2></div><span>约 3 分钟</span></div>
        <label htmlFor="subject-name">如何称呼这个主体 <b>必填</b></label>
        <input id="subject-name" name="name" value={name} onChange={(e)=>setName(e.target.value)} autoComplete="name" required />
        <label htmlFor="birth-date">出生日期 <b>必填</b></label>
        <input id="birth-date" name="birthDate" type="date" value={birthDate} onChange={(e)=>setBirthDate(e.target.value)} required />
        <div className="field-pair">
          <div><label htmlFor="birth-time">出生时刻 {!unknownTime && <b>必填</b>}</label><input id="birth-time" name="birthTime" type="time" value={birthTime} onChange={(e)=>setBirthTime(e.target.value)} disabled={unknownTime} /></div>
          <label className="check-field"><input type="checkbox" checked={unknownTime} onChange={(e)=>{setUnknownTime(e.target.checked); if(e.target.checked) setBirthTime("");}} /><span><b>出生时刻未知</b><small>系统不会补造为中午、午夜或随机时辰。</small></span></label>
        </div>
        <label htmlFor="birth-place">出生地点原文 <b>必填</b></label>
        <input id="birth-place" name="place" value={place} onChange={(e)=>setPlace(e.target.value)} placeholder="例如：中国，上海市" required />
        <label htmlFor="timezone">历史法定时区 <b>必填</b></label>
        <select id="timezone" value={timezone} onChange={(e)=>setTimezone(e.target.value)}><option>Asia/Shanghai</option><option>Asia/Hong_Kong</option><option>Asia/Taipei</option><option>UTC</option></select>
        <label className="check-field"><input type="checkbox" checked={confirmed} onChange={(e)=>setConfirmed(e.target.checked)} /><span><b>我确认以上是原始输入</b><small>太阳时校正会另行记录，不会静默改写这里的时间。</small></span></label>
        {error && <p className="field-error" role="alert" id="setup-error">{error}</p>}
        <div className="form-actions"><Link href="/" className="text-button">取消</Link><button className="product-button" disabled={status==="saving"}>{status==="saving" ? "正在保存…" : "保存资料"}</button></div>
      </form>
      <aside className="form-help"><h2>这份资料将用于什么？</h2><ul><li>保存历史法定时间与地点原文</li><li>建立机械排盘所需的候选输入</li><li>明确未知、争议与边界敏感项</li></ul><p>不会自动生成宿世身份、吉凶或应期。</p></aside>
    </div>
    {status==="error" && <PageState kind="error" title="网络连接失败"><p>你的输入仍保留在当前页面；确认连接后再次点击保存。</p></PageState>}
  </ProductShell>;
}
