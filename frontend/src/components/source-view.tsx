"use client";
import {
  FileCode2,
  FileText,
  GitCommitHorizontal,
  ArrowUpRight,
} from "lucide-react";
import { type Source } from "@/lib/demo";
export function SourceView({
  source,
  compact = false,
}: {
  source: Source;
  compact?: boolean;
}) {
  return (
    <div className={`source-view ${compact ? "compact" : ""}`}>
      <div className="source-header">
        <span>
          {source.kind === "Code" ? (
            <FileCode2 size={15} />
          ) : (
            <FileText size={15} />
          )}
          <span>{source.name}</span>
        </span>
        <span className="source-version">
          <GitCommitHorizontal size={13} />
          {source.version}
        </span>
      </div>
      <div className="code-lines">
        {source.lines.map((line, i) => (
          <div key={i} className={i === source.highlight ? "highlight" : ""}>
            <span className="line-number">
              {Number(source.location.match(/\blines?\s+(\d+)/i)?.[1] || 1) + i}
            </span>
            <code>{line}</code>
          </div>
        ))}
      </div>
      {!compact && (
        <div className="source-explanation">
          <p>{source.note}</p>
          <div className="source-location">
            {source.location}
            <ArrowUpRight size={13} />
          </div>
        </div>
      )}
    </div>
  );
}
