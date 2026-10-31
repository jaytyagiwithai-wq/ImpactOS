"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  CircleHelp,
  Download,
  FileCode2,
  GitCommitHorizontal,
  TriangleAlert,
  Undo2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import {
  investigations,
  getInvestigation,
  getSource,
  type Investigation,
} from "@/lib/demo";
import { useSources } from "@/components/workspace-shell";

const exampleLabels = [
  "Remove a webhook field",
  "Change the retry limit",
  "Check a subscriber",
];
const changeFiles = [
  "webhooks/payment.yaml",
  "payments/retry_policy.py",
  "services/catalog.yaml",
];
const diffs = [
  ["  payment_id: string", "− customer_id: string", "  amount: integer"],
  ["− MAX_RETRIES = 3", "+ MAX_RETRIES = 5", "  retry_after_seconds = 30"],
  [
    "  service: analytics",
    "+ subscribes_to: payment.completed",
    "  handler_source: not_in_snapshot",
  ],
];

export function DemoWorkspace({ reportId }: { reportId?: string }) {
  const [selected, setSelected] = useState(0);
  const [question, setQuestion] = useState(investigations[0].question);
  const [report, setReport] = useState<Investigation | null>(
    reportId ? getInvestigation(reportId) || null : null,
  );
  const inv = investigations[selected];
  const edited = question.trim() !== inv.question;
  const choose = (i: number) => {
    setSelected(i);
    setQuestion(investigations[i].question);
  };
  if (report)
    return (
      <SimpleReport
        inv={report}
        onReset={reportId ? undefined : () => setReport(null)}
      />
    );

  return (
    <div className="demo-start">
      <div className="demo-intro">
        <h1>What’s changing?</h1>
        <p>
          Choose a change, review its findings, and open the supporting files.
        </p>
      </div>
      <div className="example-picker" aria-label="Choose a sample change">
        {investigations.map((item, i) => (
          <button
            key={item.id}
            aria-pressed={selected === i}
            onClick={() => choose(i)}
          >
            {exampleLabels[i]}
          </button>
        ))}
      </div>
      <section className="change-composer" aria-label="Sample investigation">
        <div className="change-file-header">
          <span>
            <FileCode2 size={16} />
            {changeFiles[selected]}
          </span>
        </div>
        <div className="demo-diff" aria-label="Example change excerpt">
          {diffs[selected].map((line, i) => (
            <div
              key={`${selected}-${i}`}
              className={
                line.startsWith("−")
                  ? "diff-removed"
                  : line.startsWith("+")
                    ? "diff-added"
                    : ""
              }
            >
              <span>{i + 11}</span>
              <code>{line}</code>
            </div>
          ))}
        </div>
        <div className="question-area">
          <label htmlFor="change-question">What would you like to check?</label>
          <Textarea
            id="change-question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            aria-describedby={edited ? "sample-question-note" : undefined}
          />
          {edited && (
            <div className="sample-edit-note" id="sample-question-note">
              Live analysis isn’t connected. Use the sample question to view its
              report.
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setQuestion(inv.question)}
              >
                <Undo2 size={14} /> Restore question
              </Button>
            </div>
          )}
        </div>
        <div className="composer-footer">
          <span>
            <GitCommitHorizontal size={15} />
            <code>{inv.baseline}</code>
            <ArrowRight size={13} />
            <code>{inv.proposed}</code>
          </span>
          <Button
            disabled={edited || !question.trim()}
            onClick={() => {
              setReport(inv);
              window.scrollTo({ top: 0, behavior: "instant" });
            }}
          >
            View sample report <ArrowUpRight />
          </Button>
        </div>
      </section>
    </div>
  );
}

function SimpleReport({
  inv,
  onReset,
}: {
  inv: Investigation;
  onReset?: () => void;
}) {
  const { showSource } = useSources();
  const [exported, setExported] = useState(false);
  const labels = {
    confirmed: "Confirmed",
    possible: "Needs review",
    unknown: "Missing evidence",
  };
  const icons = {
    confirmed: Check,
    possible: TriangleAlert,
    unknown: CircleHelp,
  };
  const exportReport = () => {
    const content = `# ${inv.title}\n\nSynthetic sample · ${inv.id}\n${inv.baseline} → ${inv.proposed}\n\n${inv.findings
      .map(
        (f) =>
          `## ${f.title}\n${labels[f.kind]}\n\n${f.description}\n\nNext step: ${f.next}\n\nSources:\n${f.sourceIds
            .map((id) => {
              const s = getSource(id)!;
              return `- ${s.name} @ ${s.version} (${s.location})`;
            })
            .join("\n")}`,
      )
      .join("\n\n")}\n\nPrepared example; not a deployment approval.\n`;
    const url = URL.createObjectURL(
      new Blob([content], { type: "text/markdown;charset=utf-8" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${inv.id}-report.md`;
    anchor.click();
    URL.revokeObjectURL(url);
    setExported(true);
  };
  return (
    <div className="simple-report">
      <div className="report-top-actions">
        {onReset ? (
          <Button variant="ghost" size="sm" onClick={onReset}>
            <ArrowLeft /> All examples
          </Button>
        ) : (
          <Button variant="ghost" size="sm" asChild>
            <Link href="/app">
              <ArrowLeft /> All examples
            </Link>
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={exportReport}>
          <Download />
          {exported ? "Export again" : "Export report"}
        </Button>
      </div>
      <div className="simple-report-heading">
        <h1>{inv.title}</h1>
        <p>{inv.question}</p>
        <div className="simple-version">
          <GitCommitHorizontal size={15} />
          <code>{inv.baseline}</code>
          <ArrowRight size={13} />
          <code>{inv.proposed}</code>
        </div>
      </div>
      <div className="report-section-label">
        <h2>What needs checking</h2>
        <span>{inv.findings.length} findings</span>
      </div>
      <Accordion
        type="single"
        collapsible
        defaultValue={inv.findings[0].id}
        className="simple-findings"
      >
        {inv.findings.map((finding, i) => {
          const Icon = icons[finding.kind];
          return (
            <AccordionItem
              value={finding.id}
              key={finding.id}
              className={`simple-finding finding-${finding.kind}`}
            >
              <AccordionTrigger>
                <span className="finding-symbol">
                  <Icon size={17} />
                </span>
                <span className="simple-finding-name">
                  <span className="finding-status">{labels[finding.kind]}</span>
                  <strong>{finding.title}</strong>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="finding-detail">
                  <p>{finding.description}</p>
                  <div className="finding-source-links">
                    {finding.sourceIds.map((id) => {
                      const s = getSource(id)!;
                      return (
                        <Button
                          variant="outline"
                          size="sm"
                          key={id}
                          onClick={() => showSource(id)}
                        >
                          <FileCode2 size={14} />
                          <span>{s.name}</span>
                          <ArrowUpRight size={13} />
                        </Button>
                      );
                    })}
                  </div>
                  <div className="finding-next">
                    <span>Next step</span>
                    <p>{finding.next}</p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>
      <div className="report-limit">
        <CircleHelp size={16} />
        <p>Sample report based on the linked files.</p>
      </div>
    </div>
  );
}
