import "./styles.css";

export const metadata = {
  title: "三际观——宿世因缘与命势推演系统",
  description: "观因于往际，察缘于当下，见势于未来。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
