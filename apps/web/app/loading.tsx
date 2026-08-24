import ProductShell, { PageState } from "../components/ProductShell";

export default function Loading() {
  return <ProductShell title="正在安放资料" eyebrow="三际观">
    <PageState kind="loading" title="正在读取当前步骤">
      <p>只读取完成本页所需的最小资料；私人正文不会进入公开缓存。</p>
    </PageState>
  </ProductShell>;
}
