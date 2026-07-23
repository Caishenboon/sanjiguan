import AppShell from "../../../../components/AppShell";
const chain=[["宿世节点","行旅求法 · 研究候选"],["临终意识候选","此门未开：证契不足。"],["中阴倾向候选","此门未开：证契不足。"],["牵引因","愿力与业习仅作候选"],["投生环境","此门未开：证契不足。"],["今生显现","学习 · 整理 · 传播"]];
export default function Bardo(){return <AppShell title="中阴之门"><section className="panel bardo"><p className="boundary">只显示已有链结构；DeepSeek 不补齐断点，不展示 restricted 修法，不判断修行证量。</p>
 <ol>{chain.map(([h,p],i)=><li key={h} className={p.includes("未开")?"breakpoint":""}><b>{i+1}</b><div><h2>{h}</h2><p>{p}</p></div></li>)}</ol></section></AppShell>}
