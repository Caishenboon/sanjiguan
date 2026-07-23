import AppShell from "../../../../components/AppShell";import {nodes} from "../../../../lib/sprint3-fixture";
export default function Map(){return <AppShell title="宿世星图"><section className="panel map-panel"><div className="section-title"><div><p className="eyebrow">研究聚类图</p><h2>由宿世节点至今生显现</h2></div><div className="map-tools"><button>−</button><button>聚焦</button><button>＋</button></div></div>
 <svg className="samsara-svg" viewBox="0 0 760 360" role="img" aria-labelledby="map-title map-desc"><title id="map-title">宿世节点关系图</title><desc id="map-desc">六个研究节点从普通延续与世间功业，经中阴桥连接到今生与显现。</desc>
 {[[0,3],[1,3],[3,2],[2,4],[2,5]].map(([a,b],i)=><line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} className={i<2?"dashed":""}/>)}
 {nodes.map(n=><g key={n.id} tabIndex={0} aria-label={`${n.label}，${n.type}`}><circle cx={n.x} cy={n.y} r={n.r}/><text x={n.x} y={n.y+4}>{n.label}</text></g>)}</svg></section>
 <section className="panel list-alternative"><h2>列表替代视图</h2>{nodes.map(n=><button key={n.id}><b>{n.label}</b><span>{n.type}</span><small>查看证契、逆证与今生映射</small></button>)}</section></AppShell>}
