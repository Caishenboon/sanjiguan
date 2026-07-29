import Link from "next/link";
import ProductShell, { PageState } from "../../components/ProductShell";
export default function Page(){return <ProductShell title="没有访问权限" eyebrow="权限边界"><PageState kind="forbidden" title="研究后台只对授权角色开放"><p>普通用户可以继续记录、使用机械工具和阅读自己的三际录。</p><Link className="product-button" href="/">返回首页</Link></PageState></ProductShell>}
