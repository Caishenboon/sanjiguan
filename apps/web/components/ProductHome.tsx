"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductShell, { PageState } from "./ProductShell";
import { ProductSession, apiRequest, readProductSession } from "../lib/product-session";

type ArchiveItem={id:string;title:string;entry_type:string;created_at:string};
type DivinationItem={id:string;divination_at:string};

export default function ProductHome() {
  const [session, setSession] = useState<ProductSession>({ chronicles: [] });
  const [ready, setReady] = useState(false);
  const [latest, setLatest] = useState<ArchiveItem>();
  const [latestTool, setLatestTool] = useState<DivinationItem>();
  useEffect(() => {
    const refresh = () => {
      const current=readProductSession();setSession(current);setReady(true);
      if(current.subject?.id){
        apiRequest<{items:ArchiveItem[]}>(`/api/v1/chronicle?profile_id=${current.subject.id}`).then(v=>setLatest(v.items[0])).catch(()=>setLatest(undefined));
        apiRequest<{items:DivinationItem[]}>(`/api/v1/profiles/${current.subject.id}/divinations`).then(v=>setLatestTool(v.items[0])).catch(()=>setLatestTool(undefined));
      }
    };
    refresh();
    window.addEventListener("sanjiguan:session-change", refresh);
    return () => window.removeEventListener("sanjiguan:session-change", refresh);
  }, []);

  return <ProductShell title={session.subject ? `欢迎回来，${session.subject.name}` : "从如实立卷开始"} eyebrow="首页 · 观三际">
    <section className="product-hero">
      <div className="home-manifesto"><p className="product-kicker">往际 · 当下 · 未来</p><h2>先把事实安放好，<br/>再察其间的关系。</h2>
      <p>三际观保存原始资料、机械结构和版本边界。未知不会被补造，研究不会被说成定论。</p><div className="home-axis" aria-label="三际观察轴"><span><b>往</b>已有记录</span><i/><span><b>今</b>当前观照</span><i/><span><b>来</b>规则推演</span></div></div>
      <div className="home-observatory">
        <div className="home-celestial" aria-hidden="true"><i/><i/><i/><span className="home-celestial__past">往</span><span className="home-celestial__now">今</span><span className="home-celestial__future">来</span><b>三际</b><small>观其因 · 察其缘 · 见其势</small></div>
        {!ready ? <PageState kind="loading" title="正在读取个人空间"><p>只读取当前安全会话所需的最小摘要。</p></PageState> :
         !session.subject ? <PageState kind="empty" title="还没有三际录"><p>先为自己立卷。出生时刻不知道也可以如实选择“未知”，系统不会补造。</p></PageState> :
         <PageState kind="success" title="主体资料已建立"><p>{session.subject.name} · 出生时刻精度：{session.subject.timePrecision === "unknown" ? "未知" : "已记录"}</p></PageState>}
      </div>
    </section>

    <section className="home-actions-section" aria-labelledby="home-actions">
      <div className="product-section-head"><div><p className="eyebrow">现在可以做</p><h2 id="home-actions">选择一个清楚的下一步</h2></div></div>
      <div className="action-grid">
        <Link className="action-card action-card--primary" href="/onboarding"><span>01</span><h3>{session.subject ? "完善三际录" : "建立三际录"}</h3><p>约 3 分钟 · 未知项可以如实留空</p><b>{session.subject ? "继续立卷" : "开始立卷"}</b></Link>
        <Link className="action-card" href="/records"><span>02</span><h3>记录一件事</h3><p>约 1–3 分钟 · 随时可撤销</p><b>选择记录类型</b></Link>
        <Link className="action-card" href="/consult"><span>03</span><h3>开始一次合参</h3><p>先查看工具所需资料与当前状态</p><b>查看工具</b></Link>
      </div>
    </section>

    <section className="product-dashboard" aria-labelledby="recent-heading">
      <div className="product-section-head"><div><p className="eyebrow">最近状态</p><h2 id="recent-heading">从上次停下的地方继续</h2></div></div>
      <article><small>最近记录</small><h3>{latest?.title || "尚无记录"}</h3><p>{latest ? `${latest.created_at.slice(0,10)} · 数据库三际录` : "写下梦境、愿向、事件或一段观照。"}</p><Link href="/chronicle">打开三际录</Link></article>
      <article><small>最近工具</small><h3>{latestTool?"易经三钱机械结果":"尚未执行"}</h3><p>{latestTool ? "机械结果已经保存，可继续阅读。" : "易经、八字与紫微会标注机械或研究边界。"}</p><Link href={latestTool ? `/results/${latestTool.id}` : "/consult"}>{latestTool ? "继续阅读" : "查看合参"}</Link></article>
      <article><small>需要补充</small><h3>{session.subject?.timePrecision === "unknown" ? "出生时刻仍未知" : session.subject ? "可继续记录长期事实" : "主体基本资料"}</h3><p>未知值保持未知，不会自动填成中午、午夜或随机时辰。</p><Link href={session.subject ? "/records" : "/onboarding"}>去补充</Link></article>
    </section>
    {session.pendingTask && <section className="continue-task"><div><small>未完成任务</small><h2>{session.pendingTask.label}</h2></div><Link className="product-button" href={session.pendingTask.href}>继续上次任务</Link></section>}

    {!session.subject && <section className="public-overview" aria-labelledby="public-overview-title">
      <header className="public-overview__hero">
        <p className="eyebrow">三际观 · 1.0.0-rc.1</p>
        <p>三际观——宿世因缘与命势推演系统</p>
        <h2 id="public-overview-title">观因于往际，察缘于当下，见势于未来。</h2>
        <p className="public-positioning">三际观以可追溯的资料、明确的方法边界和确定性计算，连接传统结构与个人生命观照。</p>
        <p><strong>三际枢负责计算、证据融合与成断；DeepSeek仅将既定结果写成象辞。</strong></p>
        <div className="public-overview__actions"><Link className="product-button" href="/start">建立三际录</Link><Link className="secondary-button" href="/about">查看方法边界</Link></div>
        <p className="research-disclaimer">当前为工程候选版本；所有传统与三际原创规则仍处于未经审校的研究阶段。</p>
      </header>

      <section aria-labelledby="capabilities-title"><h2 id="capabilities-title">它能看什么</h2>
        <div className="public-capability-grid">
          {[
            ["八字结构","多 Profile 的机械与传统结构研究"],["紫微命盘","受限三合机械研究 Profile"],
            ["实物三钱与六爻","2/3 规范输入与版本化纳甲结构"],["六象合参","三际原创证据融合"],
            ["宿世星图","带认识状态的候选结构"],["中阴之门","人生与离世过渡双模式"],
            ["命势长图","可追溯的时序与人生 K 线"],["缘契图","遵守单方与双方同意边界"],
            ["三际断章","确定性报告与可选受控成文"],["Replay","按原输入、规则和版本重放"],
          ].map(([name,detail])=><article key={name}><h3>{name}</h3><p>{detail}</p></article>)}
        </div>
      </section>

      <section aria-labelledby="workflow-title"><h2 id="workflow-title">它如何工作</h2>
        <ol className="public-workflow">
          <li><b>立卷</b><span>保存用户确认的原始资料与精度</span></li><li><b>排盘</b><span>按明确 Profile 生成机械结构</span></li>
          <li><b>取证</b><span>引用记录、来源、证契、逆证与缺失</span></li><li><b>合参</b><span>同源去重，并区分象势与证契完备度</span></li>
          <li><b>成断</b><span>规则引擎形成版本化结构结论</span></li><li><b>观照</b><span>保存三际录，并支持复演与重观</span></li>
        </ol>
      </section>

      <section aria-labelledby="not-ai-title"><h2 id="not-ai-title">为什么 AI 不能代替术数计算</h2>
        <p>同一份输入、同一套方法与同一版本会产生相同结构结果。每项判断保留证契、逆证、冲突和缺失；AI 无权修改排盘、分数、排名、吉凶、应期或认识状态。技术版本与校验值可在“方法与版本”中核对。</p>
      </section>

      <section aria-labelledby="boundary-title"><h2 id="boundary-title">传统与原创边界</h2>
        <dl className="public-boundary-list"><div><dt>传统机械规则</dt><dd>排盘与可复现结构，来源和 Profile 可追溯。</dd></div><div><dt>流派特定解释</dt><dd>必须单独标注；争议规则不冒充唯一正统。</dd></div><div><dt>三际原创融合</dt><dd>六象、专题与命势合参属于原创研究，不伪称经典既有算法。</dd></div><div><dt>DeepSeek 成文</dt><dd>只润色白名单文本；越权即拒绝并回退确定性模板。</dd></div></dl>
        <p>当前相关规则均处于“研究态、未经审校、不可作为生产共识”的状态；技术原值保留在方法详情中。</p>
      </section>

      <section aria-labelledby="privacy-title"><h2 id="privacy-title">隐私与数据主权</h2>
        <p>系统采用邀请制、私人档案、字段加密、PostgreSQL FORCE RLS、可验证导出和明确删除语义。出生、关系、梦境与修行资料不会进入公开数据或模型训练材料；robots.txt 不是权限控制，私人页面同时依赖鉴权、no-store 与 noindex。</p>
      </section>

      <section aria-labelledby="open-source-title"><h2 id="open-source-title">开源状态</h2>
        <p>当前是工程 RC，仓库仍为 Private。代码许可证候选为 AGPL-3.0-or-later，原创规则与方法资产候选为 CC BY-SA 4.0；两者均未获最终书面批准，不代表已经开源。</p>
      </section>

      <section aria-labelledby="summary-title"><h2 id="summary-title">中文与 English summary</h2>
        <p>三际观以确定性核心、版本化规则和私人档案连接传统结构与原创研究。</p>
        <p lang="en">SanjiGuan is a private, deterministic research system. Its versioned engine computes structured results; optional AI may only render approved prose.</p>
      </section>

      <section aria-labelledby="glossary-title"><h2 id="glossary-title">术语与常见问题</h2>
        <dl className="public-boundary-list"><div><dt>三际枢</dt><dd>独立运行的确定性算法核心。</dd></div><div><dt>方法方案</dt><dd>明确边界与流派差异的版本化配置，技术名称为 Profile。</dd></div><div><dt>规则版本</dt><dd>可校验、可审查的规则集合，技术名称为 Ruleset。</dd></div><div><dt>复演</dt><dd>按原版本重放，不使用当前可变规则。</dd></div><div><dt>研究态是否等于传统共识？</dt><dd>不等于；研究态只表示可在受限研究环境运行。</dd></div><div><dt>没有 DeepSeek 能否使用？</dt><dd>可以；完整结构和确定性报告不依赖 AI 密钥。</dd></div></dl>
      </section>
    </section>}
  </ProductShell>;
}
