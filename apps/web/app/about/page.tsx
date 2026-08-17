export const metadata={
  title:"方法边界",
  description:"三际观的传统机械、流派解释、三际原创研究与DeepSeek成文边界。",
  alternates:{canonical:"/about"},
};

export default function AboutPage() {
  return <main className="shell">
    <p className="eyebrow">关于三际观</p><h1>先立卷，再观象</h1>
    <p>三际观用于个人、小规模的长期因缘研究。它把原始资料、机械结构、用户证据和规则推演分别保存，不把叙述自动升级为事实，也不让语言模型替代确定性计算。</p>
    <section className="section"><h2>当前 V1 RC 范围</h2>
      <p>三际录、实物三钱、八字、受限三合紫微、京房纳甲六爻、六象、宿世、中阴、缘契、命势长图和三际断章已经形成研究链路。</p>
      <p>全部传统与原创规则仍为 research_active、UNCONFIRMED 且不可生产激活；工程可运行不等于传统共识或现实有效性证明。</p>
    </section>
    <section className="section"><h2>算法与成文</h2>
      <p>三际枢负责排盘、证据、排名、状态、Trace、Replay 和 Hash。DeepSeek 仅能润色白名单文字，不能改名、改盘、改分、改吉凶或删除逆证。</p>
    </section>
    <section className="section"><h2>开源和隐私</h2>
      <p>仓库仍为 Private，许可证与公开发布尚未授权。私人页面依靠鉴权、RLS、加密、no-store 与 noindex 保护，不依靠 robots.txt 保密。</p>
    </section>
  </main>;
}
