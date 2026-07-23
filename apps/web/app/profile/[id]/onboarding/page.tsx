import Onboarding from "./Onboarding";
export default async function Page({params}:{params:Promise<{id:string}>}) {
  const {id}=await params;
  return <Onboarding profileId={id}/>;
}
