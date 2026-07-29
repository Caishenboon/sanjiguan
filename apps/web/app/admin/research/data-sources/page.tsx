import { ResearchWarning, SanjiHeader, SanjiShell } from "@sanji/ui";
import { researchSources } from "../../../../lib/liuxiang-research-demo";

export default function ResearchDataSourcesPage() {
  return <SanjiShell><SanjiHeader/><main className="sanji-main">
    <section className="sanji-hero"><div><p className="sanji-kicker">Pinned public research</p>
      <h1 className="sanji-title">数据源控制台</h1>
      <p className="sanji-lede">公共研究资产与真实三际录逻辑隔离；普通 CI 不访问外网。</p></div>
      <ResearchWarning>提供方评级不等于三际观独立核验。</ResearchWarning>
    </section>
    <section className="sanji-card sanji-card--wide">
      <div className="table-wrap"><table>
        <caption>固定 Revision、许可证状态与质量边界</caption>
        <thead><tr><th>数据源</th><th>Revision</th><th>许可证审核</th><th>数据量</th><th>精度/缺失</th><th>同源组</th><th>连接器</th></tr></thead>
        <tbody>{researchSources.map(source=><tr key={source.name}>
          <td>{source.name}</td><td><code>{source.revision}</code></td><td>{source.license}</td>
          <td>{source.rows}</td><td>{source.precision}</td><td><code>{source.shared}</code></td>
          <td>{source.enabled?"启用（仅本地研究）":"禁用"}</td>
        </tr>)}</tbody>
      </table></div>
    </section>
    <section className="sanji-grid" style={{marginTop:"1rem"}}>
      <article className="sanji-card"><h2>人物关联</h2><p>18,148 / 18,148 事件使用稳定提供方 ID 精确关联。</p><p>模糊匹配 0 · 冲突 0 · 自动猜测 0</p></article>
      <article className="sanji-card"><h2>可排盘数量</h2><p>时刻精度满足：15,807</p><p>IANA/DST 来源未满足：15,807，仍需人工核验。</p></article>
      <article className="sanji-card"><h2>DreamBank</h2><p>正文未下载、未提交、未发送外部 LLM。</p><p>原始授权与再发布链闭环前保持禁用。</p></article>
    </section>
  </main></SanjiShell>;
}
