import { ResearchWarning, SanjiHeader, SanjiShell } from "@sanji/ui";

export default function ResearchControlsPage() {
  return <SanjiShell><SanjiHeader/><main className="sanji-main">
    <section className="sanji-hero"><div><p className="sanji-kicker">Counterfactual protocol</p>
      <h1 className="sanji-title">研究对照</h1>
      <p className="sanji-lede">只展示聚合覆盖、基率和置换结果；不展示具体名人的命运预测。</p></div>
      <ResearchWarning>回顾性相关不等于预测能力，合成协议结果不等于现实验证。</ResearchWarning>
    </section>
    <section className="sanji-grid">
      <article className="sanji-card"><h2>数据覆盖</h2><p>出生 15,807 · 婚恋事件 18,148</p><p>相同提供方：vedastro_org</p></article>
      <article className="sanji-card"><h2>基率 Baseline</h2><p>合成协议样例 51.00%</p><p>仅证明评估代码可重复运行。</p></article>
      <article className="sanji-card"><h2>分层置换</h2><p>100 次 · 固定 seed 20260728</p><p>中位数 49.00% · 区间 39.00%–57.00%</p></article>
      <article className="sanji-card"><h2>规则候选</h2><p>当前 0 条自动晋升。</p><p>任何候选默认 draft / disabled，必须人工审查。</p></article>
    </section>
    <section className="sanji-card sanji-card--wide" style={{marginTop:"1rem"}}>
      <h2>不能证明的结论</h2>
      <ul><li>不能证明六象具有现实预测力或因果效应。</li><li>不能把提供方 AA 标签当作三际观独立核验。</li>
        <li>不能依据测试集结果回写权重并继续称为盲测。</li><li>不能对在世人物生成敏感命运判断。</li></ul>
    </section>
  </main></SanjiShell>;
}
