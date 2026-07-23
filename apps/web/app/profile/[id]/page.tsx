import Link from "next/link";

export default function ProfilePage() {
  return <main className="shell">
    <p className="eyebrow">个人长期档案</p><h1>三际录</h1>
    <p className="demo"><span className="badge">DEMO</span> 示例档案，不含真实个人资料或推演结果。</p>
    <section className="section"><h2>基础信息</h2><p>出生资料：尚未确认</p><p>分析版本：0</p></section>
    <nav className="grid" aria-label="档案功能">
      <Link className="card" href="/profile/demo/analysis">六象合参</Link>
      <Link className="card" href="/profile/demo/report">三际断章</Link>
      <Link className="card" href="/profile/demo/samsara-map">宿世星图</Link>
      <Link className="card" href="/profile/demo/life-chart">命势长图</Link>
      <Link className="card" href="/profile/demo/relationships">缘契图</Link>
      <Link className="card" href="/profile/demo/journal">观照录</Link>
      <Link className="card" href="/profile/demo/versions">历次命卷</Link>
    </nav>
  </main>;
}
