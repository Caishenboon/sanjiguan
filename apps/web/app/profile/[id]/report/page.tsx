import AppShell from "../../../../components/AppShell";
const reportOrder=["断章","象名","象辞","释义","应期","吉凶","证契","逆证"] as const;
const sections=[["宿世主象","此世主象已立：行旅求法，学成待传。"],["次象与余象","百工积累为次象，普通生计不是低位身份，而是稳定此生的现实根基。"],
["宿世节点","节点只表达研究聚类，不对应具体人物、时代或地域。"],["愿力","整理所学并传授，是现有资料中最稳定的愿向。"],
["业习","其利在持久，其险在求全与迟疑。"],["中阴链与断点","此门未开：证契不足。"],["今生映射","学习、整理与公开表达形成连续事件链。"],
["证契","异地学习、长期笔记与实际讲授相互印证。"],["逆证","传播受众尚未稳定，过早扩张会伤及深度。"],
["普通现实解释","持续学习形成了专业积累，下一阶段应先完善内容，再扩大传播。"],["待验资料","补充更早记录和长期教化事实后复核。"]];
export default function Report(){void reportOrder;return <AppShell title="三际断章" owner><article className="report"><header className="report-hero"><p className="eyebrow">总断 · RESEARCH · FIXTURE / DEMO</p><small>以下为完全虚构界面数据，不代表任何真实推演结果。</small><p className="field-label">断章</p>
 <h3>象名</h3><h2>行旅求法，学成待传</h2><h3>象辞</h3>
 <blockquote>旧卷随行多年，所经之地虽异，所问之事却始终如一。卷帙渐成，路将由求法转向传法；火候未足，现阶段宜守其深，不宜争其广。</blockquote>
 <h3>释义</h3><p>主断已立：长期修学与整理已形成清楚主线，下一阶段由求知转向有边界的传播。现有证契支持这一方向；其险在受众与内容尚未同时稳固，现阶段先守深度。</p>
 <dl><div><dt>应期</dt><dd>中程积累后</dd></div><div><dt>吉凶</dt><dd>利中有戒</dd></div><div><dt>行止</dt><dd>守</dd></div><div><dt>置信</dt><dd>研究成断</dd></div></dl></header>
 {sections.map(([h,p],i)=><section className="chapter" key={h}><span>{String(i+1).padStart(2,"0")}</span><div><h2>{h}</h2><p>{p}</p></div></section>)}
 <details className="technical"><summary>Owner 技术细节</summary><pre>{`Ruleset 0.1.0-research\nPrompt style-review-1.1\nProvider template\nFallback false\nLocked hash verified\nClaims: approved summaries only`}</pre></details></article></AppShell>}
