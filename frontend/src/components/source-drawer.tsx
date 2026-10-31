"use client";

import { ArrowLeft, ArrowUpRight, FileCode2, FileText } from "lucide-react";
import { sources, getSource } from "@/lib/demo";
import { SourceView } from "@/components/source-view";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

export function SourceDrawer({
  open,
  onOpenChange,
  sourceId,
  onSelect,
  onReturnFocus,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceId: string | null;
  onSelect: (id: string | null) => void;
  onReturnFocus: () => void;
}) {
  const source = sourceId ? getSource(sourceId) : undefined;
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        className="demo-source-sheet"
        aria-describedby="source-sheet-description"
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          onReturnFocus();
        }}
      >
        <SheetHeader>
          <SheetTitle>
            {source ? source.name.split("/").at(-1) : "Source files"}
          </SheetTitle>
          <SheetDescription id="source-sheet-description">
            {source
              ? `${source.kind} · ${source.version} · ${source.location}`
              : `${sources.length} files used by the sample reports.`}
          </SheetDescription>
        </SheetHeader>
        <div className="source-drawer-body">
          {source ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onSelect(null)}
                className="source-back"
              >
                <ArrowLeft /> All sources
              </Button>
              <SourceView source={source} />
            </>
          ) : (
            <div className="demo-source-list">
              {sources.map((s) => (
                <button
                  key={s.id}
                  onClick={() => onSelect(s.id)}
                  className="demo-source-row"
                >
                  <span className="source-file-symbol">
                    {s.kind === "Code" || s.kind === "OpenAPI" ? (
                      <FileCode2 size={20} />
                    ) : (
                      <FileText size={20} />
                    )}
                  </span>
                  <span>
                    <strong>{s.name.split("/").at(-1)}</strong>
                    <small>{s.name}</small>
                  </span>
                  <span className="source-file-version">{s.version}</span>
                  <ArrowUpRight size={15} />
                </button>
              ))}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
