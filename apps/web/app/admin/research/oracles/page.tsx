import { ConsentPanel, OracleDiffPanel, ResearchWarning, SanjiHeader, SanjiShell } from "@sanji/ui";

export default function OracleResearch() {
 return <SanjiShell><SanjiHeader/><main className="sanji-main">
  <section className="sanji-hero"><div><p className="sanji-kicker">External differential evidence</p><h1 className="sanji-title">Oracle 差分</h1><p className="sanji-lede">固定上游版本，只比较规范化机械字段。没有投票，没有自动改规则，也不进入 Engine 哈希。</p></div><ConsentPanel checked/></section>
  <ResearchWarning>仅使用虚构或明确批准的研究输入；生产运行禁止调用 Oracle。</ResearchWarning>
  <div style={{marginTop:"1rem"}}><OracleDiffPanel status="normalized_match" engine={<><h2>三际枢</h2><p>命宫 寅 · 身宫 寅 · 土五局</p><small>Domain hash 锁定</small></>} oracle={<><h2>iztro 2.5.8</h2><p>命宫 寅 · 身宫 寅 · 土五局</p><small>外部差分，不影响结果</small></>}/></div>
  <section className="sanji-grid" style={{marginTop:"1rem"}}>{["lunar-python 1.4.8","tyme4py 1.5.0","sxtwl 2.0.7","iztro 2.5.8"].map(x=><article className="sanji-card" key={x}><h3>{x}</h3><p>版本固定 · 许可证已登记 · research-test only</p></article>)}</section>
 </main></SanjiShell>;
}
