"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ProductShell, { PageState } from "./ProductShell";
import { apiRequest, readProductSession, updateProductSession } from "../lib/product-session";

type BirthRecord = {
  calendar_type:"gregorian"|"lunar"; local_date:string; local_time:string|null;
  timezone_id:string; time_precision:"minute"|"double_hour"|"half_day"|"unknown";
  place:{label?:string|null;latitude:number;longitude:number}; user_confirmed:boolean;
};
type ProfileResponse = { id: string; display_name?:string; birth?:BirthRecord|null };
const DRAFT_KEY = "sanjiguan:onboarding-draft:v1";
const JOURNEY_STEPS = ["启卷", "出生时空", "时间校正", "梦象", "业象", "愿象", "缘象与事件", "三钱与确认"] as const;

export default function SubjectSetup() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [unknownTime, setUnknownTime] = useState(false);
  const [place, setPlace] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [calendarType, setCalendarType] = useState<"gregorian"|"lunar">("gregorian");
  const [timezone, setTimezone] = useState("Asia/Shanghai");
  const [confirmed, setConfirmed] = useState(false);
  const [status, setStatus] = useState<"idle"|"saving"|"error">("idle");
  const [error, setError] = useState("");
  const [draftSaved, setDraftSaved] = useState(false);

  useEffect(() => {
    const saved = readProductSession().subject;
    if (saved) {
      setName(saved.name);
      setBirthDate(saved.birthDate);
      setUnknownTime(saved.timePrecision === "unknown");
      apiRequest<ProfileResponse>(`/api/v1/profiles/${saved.id}`).then((profile)=>{
        if(!profile.birth)return;
        setName(profile.display_name || saved.name);
        setBirthDate(profile.birth.local_date);
        setBirthTime(profile.birth.local_time?.slice(0,5) || "");
        setUnknownTime(profile.birth.time_precision === "unknown");
        setPlace(profile.birth.place.label || "");
        setLatitude(String(profile.birth.place.latitude));
        setLongitude(String(profile.birth.place.longitude));
        setCalendarType(profile.birth.calendar_type);
        setTimezone(profile.birth.timezone_id);
        setConfirmed(profile.birth.user_confirmed);
      }).catch(()=>setError("已保留本页资料，但无法读取服务端完整出生记录。请检查连接后重试。"));
    }
  }, []);

  useEffect(() => {
    if (readProductSession().subject) return;
    try {
      const draft = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "null");
      if (!draft) return;
      setName(draft.name || ""); setBirthDate(draft.birthDate || ""); setBirthTime(draft.birthTime || "");
      setUnknownTime(Boolean(draft.unknownTime)); setPlace(draft.place || ""); setLatitude(draft.latitude || "");
      setLongitude(draft.longitude || ""); setCalendarType(draft.calendarType || "gregorian");
      setTimezone(draft.timezone || "Asia/Shanghai"); setConfirmed(Boolean(draft.confirmed)); setDraftSaved(true);
    } catch { /* A damaged local draft is ignored; the server remains authoritative. */ }
  }, []);

  useEffect(() => {
    if (!name && !birthDate && !place && !latitude && !longitude) return;
    const timer = window.setTimeout(() => {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify({name,birthDate,birthTime,unknownTime,place,latitude,longitude,calendarType,timezone,confirmed}));
      setDraftSaved(true);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [name,birthDate,birthTime,unknownTime,place,latitude,longitude,calendarType,timezone,confirmed]);

  function saveDraftNow() {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({name,birthDate,birthTime,unknownTime,place,latitude,longitude,calendarType,timezone,confirmed}));
    setDraftSaved(true);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const parsedLatitude = Number(latitude);
    const parsedLongitude = Number(longitude);
    if (!name.trim() || !birthDate || (!unknownTime && !birthTime) || !place.trim() ||
        latitude.trim() === "" || longitude.trim() === "" ||
        !Number.isFinite(parsedLatitude) || parsedLatitude < -90 || parsedLatitude > 90 ||
        !Number.isFinite(parsedLongitude) || parsedLongitude < -180 || parsedLongitude > 180 || !confirmed) {
      setError("请补全必填项并确认有效经纬度；若不知道出生时刻，请选择“出生时刻未知”。");
      return;
    }
    setStatus("saving");
    try {
      const payload = {
        display_name: name.trim(),
        consent_version: "profile-consent/1.0",
        birth: {
          calendar_type: calendarType,
          local_date: birthDate,
          local_time: unknownTime ? null : `${birthTime}:00`,
          timezone_id: timezone,
          timezone_database: "IANA",
          timezone_database_version: "2025b",
          time_precision: unknownTime ? "unknown" : "minute",
          place: { label: place.trim(), latitude: parsedLatitude, longitude: parsedLongitude, coordinate_source: "user_confirmed" },
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
      sessionStorage.removeItem(DRAFT_KEY);
      router.push("/?welcome=1");
    } catch (cause) {
      setStatus("error");
      setError(cause instanceof Error ? `保存未完成：${cause.message}。请检查网络后重试。` : "保存未完成，请检查网络后重试。");
    }
  }

  return <ProductShell title="八步立卷" eyebrow="立卷 · 第 1—3 步" status="私人草稿">
    <nav className="journey-progress" aria-label="八步立卷进度">
      <header><strong>当前：启卷与出生时空</strong><span>第 1—3 步，共 8 步</span></header>
      <ol>{JOURNEY_STEPS.map((step,index)=><li key={step} className={index<3?"is-complete":undefined} aria-current={index===0?"step":undefined}>{index+1}. {step}</li>)}</ol>
    </nav>
    <div className="form-layout">
      <form className="product-form" onSubmit={submit} noValidate>
        <div className="product-section-head"><div><p className="eyebrow">启卷 · 出生时空 · 时间确认</p><h2>只记录你确认过的原始资料</h2><p>这些资料用于建立排盘输入与边界候选；梦象、业象、愿象和缘象将在后续记录中继续。</p></div><span aria-live="polite">{draftSaved?"草稿已保存在本机":"正在准备草稿"}</span></div>
        <label htmlFor="subject-name">如何称呼这个主体 <b>必填</b></label>
        <input id="subject-name" name="name" value={name} onChange={(e)=>setName(e.target.value)} autoComplete="name" required />
        <label htmlFor="birth-date">出生日期 <b>必填</b></label>
        <input id="birth-date" name="birthDate" type="date" value={birthDate} onChange={(e)=>setBirthDate(e.target.value)} required />
        <label htmlFor="calendar-type">历法类型 <b>必填</b></label>
        <select id="calendar-type" value={calendarType} onChange={(e)=>setCalendarType(e.target.value as "gregorian"|"lunar")}><option value="gregorian">公历</option><option value="lunar">农历（仅保存原始历法声明）</option></select>
        <div className="field-pair">
          <div><label htmlFor="birth-time">出生时刻 {!unknownTime && <b>必填</b>}</label><input id="birth-time" name="birthTime" type="time" value={birthTime} onChange={(e)=>setBirthTime(e.target.value)} disabled={unknownTime} /></div>
          <label className="check-field"><input type="checkbox" checked={unknownTime} onChange={(e)=>{setUnknownTime(e.target.checked); if(e.target.checked) setBirthTime("");}} /><span><b>出生时刻未知</b><small>系统不会补造为中午、午夜或随机时辰。</small></span></label>
        </div>
        <label htmlFor="birth-place">出生地点原文 <b>必填</b></label>
        <input id="birth-place" name="place" value={place} onChange={(e)=>setPlace(e.target.value)} placeholder="例如：中国，上海市" required />
        <div className="field-pair">
          <div><label htmlFor="birth-longitude">经度 <b>必填</b></label><input id="birth-longitude" name="longitude" type="number" min="-180" max="180" step="0.000001" value={longitude} onChange={(e)=>setLongitude(e.target.value)} placeholder="例如：121.473700" required /></div>
          <div><label htmlFor="birth-latitude">纬度 <b>必填</b></label><input id="birth-latitude" name="latitude" type="number" min="-90" max="90" step="0.000001" value={latitude} onChange={(e)=>setLatitude(e.target.value)} placeholder="例如：31.230400" required /></div>
        </div>
        <p className="inline-warning">经纬度必须由你确认；系统不会用 0,0 或其他占位值代替未知地点。</p>
        <label htmlFor="timezone">历史法定时区 <b>必填</b></label>
        <select id="timezone" value={timezone} onChange={(e)=>setTimezone(e.target.value)}><option>Asia/Shanghai</option><option>Asia/Hong_Kong</option><option>Asia/Taipei</option><option>UTC</option></select>
        <label className="check-field"><input type="checkbox" checked={confirmed} onChange={(e)=>setConfirmed(e.target.checked)} /><span><b>我确认以上是原始输入</b><small>太阳时校正会另行记录，不会静默改写这里的时间。</small></span></label>
        {error && <p className="field-error" role="alert" id="setup-error">{error}</p>}
        <div className="form-actions"><Link href="/" className="text-button" onClick={saveDraftNow}>暂存退出</Link><button className="product-button" disabled={status==="saving"}>{status==="saving" ? "正在保存三际录…" : "确认并继续立卷"}</button></div>
      </form>
      <aside className="form-help"><h2>为什么需要这些资料？</h2><ul><li>保存历史法定时间与地点原文</li><li>建立机械排盘所需的候选输入</li><li>并列平太阳时、视太阳时与边界差异</li><li>明确未知、争议与方法方案</li></ul><p><b>隐私：</b>出生资料属于私人敏感信息，只通过安全会话写入你的三际录。</p><p>不会自动生成宿世身份、吉凶或应期，也不会调用 DeepSeek。</p></aside>
    </div>
    {status==="error" && <PageState kind="error" title="网络连接失败"><p>你的输入仍保留在当前页面；确认连接后再次点击保存。</p></PageState>}
  </ProductShell>;
}
