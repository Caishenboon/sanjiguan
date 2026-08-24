import Link from "next/link";
import ProductShell, { PageState } from "../../components/ProductShell";

export default function OfflinePage() {
  return <ProductShell title="当前处于离线状态" eyebrow="三际观 · 离线壳层">
    <PageState kind="error" title="暂时无法连接三际观服务" action={<Link className="product-button" href="/">连接后返回首页</Link>}>
      <p>为保护私人资料，三际观不会把三际录、报告、出生资料、梦境或关系内容缓存到离线页面。未提交表单仍留在原页面，连接恢复后可以继续。</p>
    </PageState>
  </ProductShell>;
}
