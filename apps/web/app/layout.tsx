import "@fontsource/noto-sans-sc/400.css";
import "@fontsource/noto-sans-sc/500.css";
import "@fontsource/noto-sans-sc/700.css";
import "@fontsource/noto-serif-sc/400.css";
import "@fontsource/noto-serif-sc/500.css";
import "@fontsource/noto-serif-sc/700.css";
import "@fontsource/noto-sans-mono/400.css";
import "@fontsource/noto-sans-mono/700.css";
import "./styles.css";
import "@sanji/ui/styles.css";
import ServiceWorkerRegistration from "../components/ServiceWorkerRegistration";

export const metadata = {
  title: "三际观——宿世因缘与命势推演系统",
  description: "观因于往际，察缘于当下，见势于未来。",
  manifest: "/manifest.webmanifest",
};
export const viewport={themeColor:"#080b12"};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-CN"><body><ServiceWorkerRegistration/>{children}</body></html>;
}
