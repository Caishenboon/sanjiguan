export default function ReportPage() {
  const rows = [
    ["断章", "此示例仅验证报告结构，不代表任何真实推演结果。"],
    ["象名", "同舟负愿之象"],
    ["象辞", "两舟原非同岸，却因一愿并入长河。此文为系统 Demo 创作，并非经典引文。"],
    ["释义", "示例解释用于检查现代中文可读性。"],
    ["应期", "未知；无生产规则依据。"],
    ["吉凶", "Demo 字段：不作真实判断。"],
    ["证契", "无；fixture 不含用户证据。"],
    ["逆证", "无；fixture 不含用户证据。"]
  ];
  return <main className="shell"><p className="eyebrow">最终综合报告</p><h1>三际断章</h1>
    <p className="demo"><span className="badge">FIXTURE / DEMO</span> 严禁视作真实推演。</p>
    {rows.map(([title,text]) => <section className="section" key={title}><h2>{title}</h2><p>{text}</p></section>)}
  </main>;
}
