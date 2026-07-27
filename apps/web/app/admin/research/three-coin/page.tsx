import ThreeCoinPreview from "../../../../components/ThreeCoinPreview";

export default function Page(){
 return <main className="shell">
  <p className="badge">Owner only · 研究预览 · traditional_mechanical</p>
  <h1>实物三钱确定性卦象</h1>
  <p>本页面只呈现实物投掷形成的确定性卦象，不提供正式断语。</p>
  <p>币面映射须在录入时明确为 heads=3、tails=2；系统不会随机投掷、倒置爻序或猜测旧记录。</p>
  <ThreeCoinPreview/>
 </main>
}
