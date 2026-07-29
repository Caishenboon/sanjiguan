import ChronicleDetail from "../../../components/ChronicleDetail";
export default async function Page({params}:{params:Promise<{id:string}>}){return <ChronicleDetail recordId={(await params).id}/>}
