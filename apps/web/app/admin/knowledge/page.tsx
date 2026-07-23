import Link from "next/link";
export default function KnowledgeAdmin(){
  return <main className="shell"><p className="eyebrow">三际枢 · Owner only</p><h1>知识工坊</h1>
    <p className="boundary">知识可入卷、规则可审、出处可追。本界面不激活生产术数。</p>
    <nav className="grid">
      <Link className="card" href="/admin/knowledge/documents">文献登记</Link>
      <Link className="card" href="/admin/knowledge/claims">Claim 工坊</Link>
      <Link className="card" href="/admin/knowledge/reviews">审核队列</Link>
      <Link className="card" href="/admin/source-register">来源登记册</Link>
      <Link className="card" href="/admin/rules">规则草案</Link>
      <Link className="card" href="/admin/archetypes">原型研究</Link>
    </nav></main>;
}
