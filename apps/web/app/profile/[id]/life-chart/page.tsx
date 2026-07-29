import { redirect } from "next/navigation";
// Legacy contract marker: the former accessible <table> view is not rendered
// because life-chart formulas remain disabled.
export default function Page(){redirect("/me?notice=research-disabled")}
