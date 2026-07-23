const systems = [
  ["命象", "规则待定"], ["卦象", "规则待定"], ["业象", "尚未成断"],
  ["愿象", "尚未成断"], ["梦象", "尚未成断"], ["缘象", "尚未成断"]
];
export default function AnalysisPage() {
  return <main className="shell"><p className="eyebrow">综合分析过程</p><h1>六象合参</h1>
    <p className="demo"><span className="badge">DEMO</span> 本页只显示模块状态，不代表已完成计算。</p>
    <div className="systems">{systems.map(([name,status]) =>
      <section className="card" key={name}><h2>{name}</h2><p>{status}</p></section>)}</div>
  </main>;
}
