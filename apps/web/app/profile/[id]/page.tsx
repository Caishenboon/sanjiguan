import Link from "next/link";
export default async function ProfilePage({params}:{params:Promise<{id:string}>}) {
  const {id}=await params;
  return <main className="shell">
    <p className="eyebrow">三际录</p><h1>个人因缘档案</h1>
    <p className="boundary">当前为证据采集阶段，术数规则尚未开卷。</p>
    <section className="section"><h2>资料完整度</h2>
      <p>命象、梦象、感应象、业象、愿象、缘象、世象分别显示未填写、未知、明确没有、不适用或已填写。</p>
      <small>完整度仅表示资料就绪程度，不是命运、修行或宿世评分。</small>
    </section>
    <section className="section"><h2>最近入卷</h2><p>暂无证据。新增记录后会按发生时间与记录时间分别排列。</p></section>
    <nav className="grid" aria-label="档案功能">
      <Link className="card" href={`/profile/${id}/onboarding`}>继续八步立卷</Link>
      <Link className="card" href={`/profile/${id}/journal`}>修行日志</Link>
      <Link className="card" href={`/profile/${id}/relationships`}>关系同意</Link>
      <Link className="card" href={`/profile/${id}/analysis`}>受阻分析</Link>
    </nav>
  </main>;
}
