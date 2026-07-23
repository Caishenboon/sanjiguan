import AppShell from "../../../../components/AppShell";

const versions = [
  { version: "卷三", date: "2026-07-23", status: "研究成断", ruleset: "0.1.0-research", change: "补入长期事件与逆证复核" },
  { version: "卷二", date: "2026-07-18", status: "两象相争", ruleset: "0.1.0-research", change: "愿象与世象主次仍待分辨" },
  { version: "卷一", date: "2026-07-12", status: "不成断", ruleset: "0.1.0-research", change: "资料不足，仅完成证据归档" },
];

export default function VersionsPage() {
  return <AppShell title="历次命卷" owner>
    <section className="panel">
      <div className="section-title">
        <div><p className="eyebrow">版本封存</p><h2>命卷沿革</h2></div>
        <small>虚构 fixture · 不代表真实推演</small>
      </div>
      <p>版本只记录当时可核查的资料、规则和结论状态；后续补证不会静默覆盖旧卷。</p>
    </section>
    <section className="panel">
      <div className="table-wrap">
        <table>
          <thead><tr><th>版本</th><th>封存日期</th><th>结论状态</th><th>Ruleset</th><th>主要变化</th></tr></thead>
          <tbody>{versions.map(item => <tr key={item.version}>
            <th scope="row">{item.version}</th><td>{item.date}</td><td>{item.status}</td>
            <td><code>{item.ruleset}</code></td><td>{item.change}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </section>
    <section className="panel empty-state" aria-live="polite">
      <h2>版本比较仍为只读研究能力</h2>
      <p>本阶段展示版本脉络与变化摘要，不提供自动重算、生产结论或未冻结术数差异。</p>
    </section>
  </AppShell>;
}
