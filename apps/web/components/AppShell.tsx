import Link from "next/link";
const mainNav=[["三际录","/profile/demo"],["六象合参","/profile/demo/analysis"],
["三际断章","/profile/demo/report"],["宿世星图","/profile/demo/samsara-map"],
["中阴之门","/profile/demo/bardo"],["命势长图","/profile/demo/life-chart"],
["缘契图","/profile/demo/relationships"],["观照录","/profile/demo/journal"],
["历次命卷","/profile/demo/versions"]];
const ownerNav=[["研究推演","/admin/research/analyses"],["实物三钱","/admin/research/three-coin"],["知识工坊","/admin/knowledge"],
["规则工坊","/admin/rules"],["评测","/admin/evaluations"]];
export default function AppShell({children,title,owner=false}:{children:React.ReactNode,title:string,owner?:boolean}){
 return <div className="app-shell">
  <aside className="sidebar"><Link href="/" className="brand"><span>三际观</span><small>大屏观三际</small></Link>
   <nav aria-label="核心导航">{mainNav.map(([n,h])=><Link key={n} href={h}>{n}</Link>)}</nav>
   {owner&&<nav className="owner-nav" aria-label="Owner 工具"><p>OWNER</p>{ownerNav.map(([n,h])=><Link key={n} href={h}>{n}</Link>)}</nav>}
  </aside>
  <div className="app-main"><header className="topbar"><button className="mobile-menu" aria-label="打开导航">☰</button>
   <div><p className="eyebrow">研究命卷</p><h1>{title}</h1></div><span className="status-dot">研究预览</span></header>
   <main className="content">{children}</main></div>
  <nav className="mobile-nav" aria-label="手机导航">
   <Link href="/profile/demo">命卷</Link><Link href="/profile/demo/journal">速记</Link>
   <Link href="/profile/demo/report">断章</Link><Link href="/profile/demo/analysis">进度</Link><Link href="/profile/demo/more">更多</Link>
  </nav>
 </div>
}
