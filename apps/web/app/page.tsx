import ProductHome from "../components/ProductHome";

export default function HomePage() {
  const origin=process.env.PUBLIC_ORIGIN||"http://127.0.0.1:3000";
  const structuredData={
    "@context":"https://schema.org",
    "@type":"SoftwareApplication",
    name:"三际观",
    alternateName:"SanjiGuan",
    applicationCategory:"LifestyleApplication",
    operatingSystem:"Web",
    url:origin,
    softwareVersion:"1.0.0-rc.1",
    description:"融合传统术数结构、三际原创证据合参与生命轨迹观照的确定性私人研究系统。",
    isAccessibleForFree:true,
  };
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(structuredData).replace(/</g,"\\u003c")}}/><ProductHome /></>;
}
