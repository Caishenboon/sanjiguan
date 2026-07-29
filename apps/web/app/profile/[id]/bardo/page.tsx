import { redirect } from "next/navigation";
// 待命理规则入枢：中阴功能保持禁用，不返回占位推演。
export default function Page(){redirect("/me?notice=research-disabled")}
