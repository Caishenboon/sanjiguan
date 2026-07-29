import ResultReader from "../../../components/ResultReader";
export default async function Page({params}:{params:Promise<{id:string}>}){return <ResultReader runId={(await params).id}/>}
