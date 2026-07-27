import Link from "next/link";
import BaziResearchPreview from "../../../../components/BaziResearchPreview";

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
  <p className="badge">Owner only · 机械排盘研究 · UNCONFIRMED</p>
  <h1>八字多 Profile 四柱研究台</h1>
  <p className="boundary">可显式选择研究 Profile 生成基础四柱、边界候选与 Replay。结果不是生产命盘，不含十神、旺衰、吉凶或任何解释。</p>
  <section className="panel">
   <h2>候选 Method Profile</h2>
   <ul>{profiles.map(([id,label])=><li key={id}><strong>{label}</strong><br/><code>{id}</code></li>)}</ul>
   <p>每次执行必须同时提交 Profile ID 与版本；未选择时拒绝执行，不存在隐藏默认方法。</p>
  </section>
  <section className="panel">
   <h2>边界案例资产</h2>
   <ul>{categories.map(([name,count])=><li key={name}>{name}：{count} 例</li>)}</ul>
   <p>共 74 个完全合成边界案例已接入真实引擎验证；待人工审校案例不冒充权威金样例。</p>
  </section>
  <section className="panel">
   <h2>证据与审校</h2>
   <p>当前登记 12 项 Claim、10 个 Locator。传统文本、工程事实、Owner 决定和证据缺口分别标注。</p>
   <p>D-002、D-003 仍未冻结；当前仅为可回放的机械研究实现，需要合格八字方法审校人和逐例签字金样例。</p>
   <p><Link href="/admin/knowledge/claims">前往 Claim 工坊记录审校意见</Link> ·
    <Link href="/admin/knowledge/reviews"> 查看审查流程</Link></p>
  </section>
  <section className="panel">
   <h2>研究执行入口</h2>
   <p>API：<code>POST /api/v1/admin/research/bazi-four-pillars/execute</code>；比较：<code>/compare</code>。可查看时间修正链、候选四柱、Trace 摘要、版本及哈希，并保存 Replay Manifest。</p>
   <p>正式启用前仍须另行冻结方法、提升版本、补审校责任人并重新运行全部门禁。</p>
  </section>
  <BaziResearchPreview/>
 </main>
}
