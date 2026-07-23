import Link from "next/link";

export default function HomePage() {
  return (
    <main className="home">
      <div className="orbit" aria-hidden="true" />
      <p className="eyebrow">过去 · 当下 · 未来</p>
      <h1>三际观</h1>
      <p className="subtitle">宿世因缘与命势推演系统</p>
      <blockquote>观因于往际，察缘于当下，见势于未来。</blockquote>
      <p className="boundary">当前仅开放工程基础与档案记录；未审校规则不会产生术数结论。</p>
      <nav className="actions" aria-label="主要入口">
        <Link className="primary" href="/profile/demo">开始观命</Link>
        <Link className="secondary" href="/profile/demo">续观三际录</Link>
      </nav>
    </main>
  );
}
