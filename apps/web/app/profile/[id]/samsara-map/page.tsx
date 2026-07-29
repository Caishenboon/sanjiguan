import { redirect } from "next/navigation";
// Legacy accessibility contract: the former “列表替代视图” is retired with this
// synthetic page and the URL now moves into the permission-aware product spine.
export default function Page(){redirect("/me?notice=research-disabled")}
