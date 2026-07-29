import RecordForm from "../../../components/RecordForm";

export default async function Page({ searchParams }: { searchParams: Promise<{ type?: string }> }) {
  const type = (await searchParams).type || "life_event";
  return <RecordForm requestedType={type} />;
}
