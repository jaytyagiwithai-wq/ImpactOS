import { notFound } from "next/navigation";
import { DemoWorkspace } from "@/components/demo-workspace";
import { getInvestigation, investigations } from "@/lib/demo";
export function generateStaticParams() {
  return investigations.map((i) => ({ id: i.id }));
}
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const inv = getInvestigation(id);
  if (!inv) notFound();
  return <DemoWorkspace key={id} reportId={id} />;
}
