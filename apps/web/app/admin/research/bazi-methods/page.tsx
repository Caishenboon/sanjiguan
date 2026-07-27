import Link from "next/link";

const profiles=[
 ["BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1","法定时间／民用午夜候选"],
 ["BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1","地方视太阳时／子初候选"],
 ["BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1","双轨敏感性／早晚子时候选"],
];
const categories=[
 ["时间与时区",8],["年界",4],["月界",38],["日界",7],["时界与未知时间",17],
];

export default function Page(){
 return <main className="shell">
  <p className="badge">Owner only · 方法研究 · 不生成四柱</p>
  <h1>八字基础排盘方法冻结工作台</h1>
  <p className="boundary">全部档案仅用于分歧比较，均不可激活生产。页面不计算年柱、月柱、日柱或时柱。</p>
  <section className="panel">
   <h2>候选 Method Profile</h2>
   <ul>{profiles.map(([id,label])=><li key={id}><strong>{label}</strong><br/><code>{id}</code></li>)}</ul>
   <p>未显式选择 Profile 时必须拒绝验证，不存在隐藏默认方法。</p>
  </section>
  <section className="panel">
   <h2>边界案例资产</h2>
   <ul>{categories.map(([name,count])=><li key={name}>{name}：{count} 例</li>)}</ul>
   <p>共 74 个完全合成案例；只断言方法政策差异，不保存或显示四柱期望值。</p>
  </section>
  <section className="panel">
   <h2>证据与审校</h2>
   <p>当前登记 12 项 Claim、10 个 Locator。传统文本、工程事实、Owner 决定和证据缺口分别标注。</p>
   <p>D-002、D-003 仍未冻结；需要合格八字方法审校人和逐例签字边界样例。</p>
   <p><Link href="/admin/knowledge/claims">前往 Claim 工坊记录审校意见</Link> ·
    <Link href="/admin/knowledge/reviews"> 查看审查流程</Link></p>
  </section>
  <section className="panel">
   <h2>产品负责人决定</h2>
   <p>本 Sprint 不代填最终决定。冻结后须另行提升 Profile 版本、补审校责任人并重新运行全部门禁。</p>
  </section>
 </main>
}
