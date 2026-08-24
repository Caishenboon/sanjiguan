"use client";

import ProductShell, { PageState } from "../components/ProductShell";

export default function ProductError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <ProductShell title="这一步暂未完成" eyebrow="三际观 · 安全恢复">
    <PageState kind="error" title="页面遇到意外状况" action={<button className="product-button" onClick={reset}>重新尝试</button>}>
      <p>未提交内容仍保留在当前页面。若再次发生，请记录页面位置和出现时间，不要发送私人正文。</p>
    </PageState>
  </ProductShell>;
}
