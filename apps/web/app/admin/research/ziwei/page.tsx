import { ProfileBadge, ResearchWarning, SanjiHeader, SanjiShell, TraceStep, ZiweiPalaceGrid } from "@sanji/ui";

const palaces = [
  {name:"命宫",branch:"寅",stars:["武曲","天相"],body:true},{name:"父母",branch:"卯",stars:["太阳","天梁"]},
  {name:"福德",branch:"辰",stars:["七杀"]},{name:"田宅",branch:"巳",stars:["天机"]},
  {name:"官禄",branch:"午",stars:["紫微"]},{name:"仆役",branch:"未",stars:[]},
  {name:"迁移",branch:"申",stars:["破军"]},{name:"疾厄",branch:"酉",stars:[]},
  {name:"财帛",branch:"戌",stars:["廉贞","天府"]},{name:"子女",branch:"亥",stars:["太阴"]},
  {name:"夫妻",branch:"子",stars:["贪狼"]},{name:"兄弟",branch:"丑",stars:["天同","巨门"]},
];
export default function ZiweiResearch() {
 return <SanjiShell><SanjiHeader/><main className="sanji-main">
  <section className="sanji-hero"><div><p className="sanji-kicker">Owner research · Ziwei</p><h1 className="sanji-title">十二宫机械盘</h1><p className="sanji-lede">受限三合基础结构。只展示可回放的宫位与星曜定位，不输出性格、吉凶或星曜解释。</p></div><div><ProfileBadge>ZIWEI.SANHE.MANUAL_LUNAR.LEAP_SAME_MONTH.V1</ProfileBadge><p>土五局 · 命身同宫寅</p></div></section>
  <ResearchWarning>traditional_mechanical · research_active · UNCONFIRMED · D-005 尚未冻结</ResearchWarning>
  <section className="sanji-card sanji-card--full" style={{marginTop:"1rem"}}><ZiweiPalaceGrid palaces={palaces}/></section>
  <section className="sanji-card sanji-card--full" style={{marginTop:"1rem"}}><TraceStep index={1} title="人工核验农历输入">自动转换关闭</TraceStep><TraceStep index={2} title="闰月与时辰 Profile">策略显式记录</TraceStep><TraceStep index={3} title="宫位、五行局、主星">纯机械定位</TraceStep><TraceStep index={4} title="Replay">资产版本与领域哈希锁定</TraceStep></section>
 </main></SanjiShell>;
}
