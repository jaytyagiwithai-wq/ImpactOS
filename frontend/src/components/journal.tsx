"use client";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  GitBranch,
  Braces,
  FileText,
} from "lucide-react";
import { motion, useScroll, useSpring } from "framer-motion";
import { PublicNav, PublicFooter } from "./landing";
import { SectionLink } from "./ui";
import { articles } from "@/lib/articles";

export function ArticleArt({ kind }: { kind: string }) {
  return (
    <div className={`article-art art-${kind}`} aria-hidden="true">
      {kind === "version" ? (
        <>
          <div className="art-version-card">
            v1<span>Active</span>
          </div>
          <span className="version-curve" />
          <div className="art-version-card second">
            v2<span>Staging</span>
          </div>
        </>
      ) : kind === "graph" ? (
        <>
          <div className="article-graph-node graph-one">
            <Braces size={24} />
            <span>API</span>
          </div>
          <div className="article-graph-node graph-two">
            <GitBranch size={24} />
            <span>Consumer</span>
          </div>
          <div className="article-graph-node graph-three">
            <FileText size={24} />
            <span>Context</span>
          </div>
          <svg
            className="article-graph-lines"
            viewBox="0 0 500 250"
            fill="none"
          >
            <path
              d="M100 100Q170 50 240 125Q320 220 400 100"
              stroke="#d59c76"
              strokeDasharray="4 5"
            />
          </svg>
        </>
      ) : (
        <>
          <div className="art-page">
            <i />
            <i />
            <i />
            <span className="art-citation">[1]</span>
          </div>
          <div className="art-source">
            Source file
            <ArrowUpRight size={16} />
          </div>
          <svg viewBox="0 0 300 180" fill="none">
            <path
              d="M180 40Q260 30 230 130H120"
              stroke="#D84931"
              strokeWidth="1.3"
              strokeDasharray="4 4"
            />
          </svg>
        </>
      )}
    </div>
  );
}
export function JournalIndex() {
  return (
    <div className="site-container" id="top">
      <PublicNav />
      <main className="journal-page">
        <div className="journal-page-heading">
          <h1>
            Think it through.
            <br />
            <em>Then make the change.</em>
          </h1>
          <p>
            Notes on evidence, source context, and the engineering decisions
            behind a useful change investigation.
          </p>
        </div>
        <div className="journal-index">
          {articles.map((a, i) => (
            <article key={a.slug} className={i === 0 ? "featured-article" : ""}>
              <Link href={`/journal/${a.slug}`}>
                <ArticleArt kind={a.art} />

                <h2>{a.title}</h2>
                <p>{a.excerpt}</p>
              </Link>
              <SectionLink href={`/journal/${a.slug}`}>
                Read the note
              </SectionLink>
            </article>
          ))}
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
export function JournalArticle({
  article,
}: {
  article: (typeof articles)[number];
}) {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });
  return (
    <div className="site-container" id="top">
      <motion.div className="reading-progress" style={{ scaleX }} />
      <PublicNav />
      <main className="article-reading">
        <Link href="/journal" className="article-back">
          <ArrowLeft size={14} />
          Back to notes
        </Link>

        <h1>{article.title}</h1>
        <p className="article-intro">{article.excerpt}</p>

        <ArticleArt kind={article.art} />
        <div className="article-body">
          {article.sections.map((s, i) => (
            <section key={s.heading}>
              <h2>{s.heading}</h2>
              <p>{s.body}</p>
              {i === 1 && <blockquote>{article.quote}</blockquote>}
            </section>
          ))}
          <p className="article-disclosure">
            These notes describe the design of the ImpactOS project. The
            workspace uses synthetic demonstration data.
          </p>
          <SectionLink href="/app/investigations/INV-014">
            Inspect the example investigation
          </SectionLink>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
