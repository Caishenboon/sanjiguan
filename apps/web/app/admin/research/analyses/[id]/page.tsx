export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <main className="shell">
<p className="badge">研究预览 · 非生产命盘</p><h1>三际断章</h1><p>分析编号：{id}</p>
<section className="section"><h2>总断与前三候选</h2><p>展示明确的 decisive、provisional、contested 或 insufficient 状态。</p></section>
<section className="section"><h2>证据、逆证与普通解释</h2><p>逆证真实扣分；重复来源不重复累计。</p></section>
<section className="section"><h2>宿世节点与中阴链断点</h2><p>缺少依据时显示“链条未成”，不由模型补齐。</p></section>
<section className="section"><h2>可回放性</h2><p>显示 Ruleset、Claim 快照、随机种子、阶段 Hash 与赋辞来源。</p></section>
</main>}
