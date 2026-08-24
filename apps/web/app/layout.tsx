import "@fontsource/noto-sans-sc/400.css";
import "@fontsource/noto-serif-sc/500.css";
import "@fontsource/noto-sans-mono/400.css";
import "./styles.css";
import "@sanji/ui/styles.css";
import ServiceWorkerRegistration from "../components/ServiceWorkerRegistration";

const publicOrigin=process.env.PUBLIC_ORIGIN||"http://127.0.0.1:3000";
export const metadata = {
  metadataBase:new URL(publicOrigin),
  title:{default:"三际观｜确定性宿世因缘与生命轨迹研究系统",template:"%s｜三际观"},
  description:"三际观以三际枢确定性核心连接传统术数结构、证据合参、宿世因缘与生命轨迹；DeepSeek仅将既定结果写成象辞。",
  manifest: "/manifest.webmanifest",
  alternates:{canonical:"/"},
  applicationName:"三际观",
  openGraph:{type:"website",locale:"zh_CN",siteName:"三际观",title:"三际观｜确定性宿世因缘与生命轨迹研究系统",description:"三际枢负责计算、证据融合与成断；DeepSeek仅将既定结果写成象辞。",url:"/"},
  twitter:{card:"summary",title:"三际观",description:"确定性传统结构与三际原创研究系统；AI不能修改结构化结论。"},
};
export const viewport={themeColor:"#080b12"};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-CN"><body><ServiceWorkerRegistration/>{children}</body></html>;
}
