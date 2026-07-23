"use client";import {useState} from "react";import AppShell from "../../../../components/AppShell";
const types=["记一梦","记一感","记一事","记一缘","记一愿"];
export default function Journal(){const [kind,setKind]=useState(types[0]);const [saved,setSaved]=useState(false);return <AppShell title="观照录"><section className="capture panel"><p className="eyebrow">小屏录一念</p><h2>三步以内，先记下来</h2>
 <div className="capture-types">{types.map(t=><button className={kind===t?"active":""} onClick={()=>setKind(t)} key={t}>{t}</button>)}</div>
 <label>发生时间<input type="datetime-local" aria-label="发生时间"/></label><label>{kind.slice(2)}的内容<textarea rows={6} placeholder="只写此刻记得的内容，稍后可以补充。"/></label>
 <div className="capture-actions"><button onClick={()=>setSaved(true)}>存为草稿</button><button className="primary-button" onClick={()=>setSaved(true)}>保存入卷</button></div>
 <p aria-live="polite">{saved?"已保留当前页面草稿 · 等待安全同步":"尚未保存"}</p><small>锁屏通知不显示正文；网络失败时只保留当前页面状态，本阶段不建立长期离线敏感数据库。</small></section></AppShell>}
