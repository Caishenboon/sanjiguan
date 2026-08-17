import ResultReader from "../../../components/ResultReader";
export default async function Page({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{traditional?:string}>}){const [route,query]=await Promise.all([params,searchParams]);return <ResultReader runId={route.id} traditionalRunId={query.traditional}/>}
