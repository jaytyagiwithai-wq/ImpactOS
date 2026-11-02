"use client";

import Link from "next/link";
import { createContext, useContext, useRef, useState } from "react";
import { ArrowUpRight, Files } from "lucide-react";
import { Logo } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { SourceDrawer } from "@/components/source-drawer";
import { sources } from "@/lib/demo";

const SourcesContext = createContext<{ showSource: (id?: string) => void }>({
  showSource: () => {},
});
export const useSources = () => useContext(SourcesContext);

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [sourceId, setSourceId] = useState<string | null>(null);
  const sourceTrigger = useRef<HTMLElement | null>(null);
  const apiMode = process.env.NEXT_PUBLIC_DATA_MODE === "api";
  const showSource = (id?: string) => {
    sourceTrigger.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    setSourceId(id || null);
    setOpen(true);
  };
  return (
    <SourcesContext.Provider value={{ showSource }}>
      <div className="simple-app">
        <a className="skip-link" href="#demo-main">
          Skip to content
        </a>
        <header className="demo-header">
          <div className="demo-header-brand">
            <Logo />
            <span className="demo-header-divider" />
            <span className="demo-header-label">Interactive demo</span>
          </div>
          <nav aria-label="Demo navigation">
            {apiMode ? (
              <span className="live-header-status"><Files size={15} /> Sources are live</span>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => showSource()}>
                <Files size={16} />
                <span>Sources</span>
                <span className="source-count">{sources.length}</span>
              </Button>
            )}
            <Button variant="ghost" size="sm" asChild>
              <Link href="/" aria-label="Back to website">
                <span>Website</span>
                <ArrowUpRight size={15} />
              </Link>
            </Button>
          </nav>
        </header>
        <main id="demo-main" className="demo-main">
          {children}
        </main>
        <footer className="demo-footer">
          <span>ImpactOS</span>
          <span>{apiMode ? "Live evidence analysis" : "Sample product preview"}</span>
        </footer>
        <SourceDrawer
          open={open}
          onOpenChange={setOpen}
          sourceId={sourceId}
          onSelect={setSourceId}
          onReturnFocus={() =>
            sourceTrigger.current?.focus({ preventScroll: true })
          }
        />
      </div>
    </SourcesContext.Provider>
  );
}
