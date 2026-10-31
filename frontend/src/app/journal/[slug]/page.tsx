import { notFound } from "next/navigation";
import { articles } from "@/lib/articles";
import { JournalArticle } from "@/components/journal";
export function generateStaticParams() {
  return articles.map((a) => ({ slug: a.slug }));
}
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = articles.find((a) => a.slug === slug);
  if (!article) notFound();
  return <JournalArticle article={article} />;
}
