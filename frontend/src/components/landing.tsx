"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowUpRight,
  Check,
  GitBranch,
  FileText,
  Braces,
  Play,
  X,
  CircleHelp,
  Menu,
} from "lucide-react";
import { Action, Logo, SectionLink, Dialog } from "./ui";
import { SourceView } from "./source-view";
import { sources } from "@/lib/demo";
import { ChangePreview, VersionDemo } from "./product-demos";

const ease = [0.16, 1, 0.3, 1] as const;
function Reveal({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-35px" }}
      transition={{ duration: 0.35, ease }}
    >
      {children}
    </motion.div>
  );
}

export function PublicNav() {
  const [menu, setMenu] = useState(false);
  return (
    <header className="public-nav">
      <Logo />
      <nav aria-label="Main navigation">
        <a href="/#investigate">The product</a>
        <a href="/#trace">How it works</a>
        <Link href="/journal">Notes</Link>
      </nav>
      <div className="nav-actions">
        <Link className="nav-login" href="/app">
          Try the demo
          <ArrowUpRight size={13} />
        </Link>
        <Action href="/app">Get started</Action>
        <button
          className="mobile-menu icon-button"
          onClick={() => setMenu(!menu)}
          aria-label="Toggle navigation"
          aria-expanded={menu}
        >
          {menu ? <X size={21} /> : <Menu size={21} />}
        </button>
      </div>
      {menu && (
        <nav className="mobile-nav">
          <a href="/#investigate" onClick={() => setMenu(false)}>
            The product
          </a>
          <a href="/#trace" onClick={() => setMenu(false)}>
            How it works
          </a>
          <Link href="/journal">Notes</Link>
          <Link href="/app">Try the demo</Link>
        </nav>
      )}
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="public-footer">
      <div>
        <Logo />
      </div>
      <div className="footer-links">
        <Link href="/app">
          Try the demo <ArrowUpRight size={13} />
        </Link>
        <Link href="/journal">
          Notes <ArrowUpRight size={13} />
        </Link>
        <a href="/#trace">
          How it works <ArrowUpRight size={13} />
        </a>
      </div>
      <div className="footer-bottom">
        <span>© 2026 ImpactOS</span>
        <span>Examples use sample data.</span>
        <a href="#top">Back to top ↑</a>
      </div>
    </footer>
  );
}

const chapters = [
  {
    number: "01",
    title: "Start with the API change.",
    body: "The schema removes customer_id from the payment.completed event.",
    detail: "OpenAPI change · customer_id removed",
    label: "The API contract",
    source: "webhooks/payment.yaml",
    description:
      "The proposed version removes a field from the payment.completed event.",
  },
  {
    number: "02",
    title: "Find the reader.",
    body: "The billing handler reads this field. Its integration manifest connects it to a customer.",
    detail: "Field → handler → integration",
    label: "The consuming service",
    source: "billing/handlers.py:86",
    description:
      "The billing adapter reads customer_id. An integration manifest connects the adapter to Customer integration.",
  },
  {
    number: "03",
    title: "Check what is missing.",
    body: "The analytics subscriber is listed, but its handler is missing. That dependency stays unconfirmed.",
    detail: "Confirmed · possible · unknown",
    label: "The review",
    source: "3 findings · 4 supporting sources",
    description:
      "Review the consumer, check customer notice requirements, and close the missing analytics evidence.",
  },
];
function DependencyStory() {
  const [active, setActive] = useState(0);
  const refs = useRef<(HTMLDivElement | null)[]>([]);
  const ticking = useRef(false);
  useEffect(() => {
    const update = () => {
      ticking.current = false;
      const center = window.innerHeight * 0.48;
      let closest = 0,
        d = Infinity;
      refs.current.forEach((el, i) => {
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const next = Math.abs(rect.top + rect.height / 2 - center);
        if (next < d) {
          d = next;
          closest = i;
        }
      });
      setActive(closest);
    };
    const scroll = () => {
      if (!ticking.current) {
        ticking.current = true;
        requestAnimationFrame(update);
      }
    };
    window.addEventListener("scroll", scroll, { passive: true });
    update();
    return () => window.removeEventListener("scroll", scroll);
  }, []);
  return (
    <section className="story-section" id="trace">
      <div className="story-heading">
        <h2>Follow the dependency.</h2>
      </div>
      <div className="story-grid">
        <div className="story-chapters">
          {chapters.map((c, i) => (
            <div
              className={`story-chapter ${active === i ? "chapter-active" : ""}`}
              key={c.number}
              ref={(el) => {
                refs.current[i] = el;
              }}
            >
              <h3>{c.title}</h3>
              <p>{c.body}</p>

              <div className="mobile-chapter-preview">
                <Braces size={22} />
                <code>{c.source}</code>
                <p>{c.description}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="story-sticky">
          <div className="story-visual">
            <div className="dependency-evidence-path">
              <div className="evidence-path-row">
                <span>
                  <Braces size={19} />
                </span>
                <div>
                  <strong>payment.completed</strong>
                  <p>customer_id removed</p>
                </div>
              </div>
              <div
                className={
                  active > 0
                    ? "evidence-path-row path-highlighted"
                    : "evidence-path-row"
                }
              >
                <span>
                  <GitBranch size={19} />
                </span>
                <div>
                  <strong>Billing handler</strong>
                  <p>Reads customer_id</p>
                </div>
              </div>
              <div
                className={
                  active > 0
                    ? "evidence-path-row path-highlighted"
                    : "evidence-path-row"
                }
              >
                <span>
                  <FileText size={19} />
                </span>
                <div>
                  <strong>Customer integration</strong>
                  <p>Connected through its manifest</p>
                </div>
              </div>
              <div className="evidence-path-row path-missing">
                <span>
                  <CircleHelp size={19} />
                </span>
                <div>
                  <strong>Analytics worker</strong>
                  <p>Handler source missing</p>
                </div>
              </div>
            </div>
            <AnimatePresence mode="wait">
              <motion.div
                className="map-explanation"
                key={active}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
              >
                <p>{chapters[active].description}</p>
                <code>{chapters[active].source}</code>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

function EvidenceDesk() {
  const [open, setOpen] = useState(false);
  return (
    <section className="evidence-section-new" id="evidence">
      <div className="evidence-heading">
        <h2>
          Read the source.
          <br />
          <em>Check the finding.</em>
        </h2>
        <p>
          Each finding links to an excerpt with its file name, version, and
          location.
        </p>
        <button className="section-link" onClick={() => setOpen(true)}>
          Inspect the source
          <ArrowUpRight size={17} />
        </button>
      </div>
      <Reveal className="evidence-desk">
        <div className="desk-finding">
          <span className="verification-mark">
            <Check size={14} />
          </span>
          <div>
            <strong>Billing reads customer_id.</strong>
          </div>
          <button
            onClick={() => setOpen(true)}
            className="icon-button"
            aria-label="Inspect billing evidence"
          >
            <ArrowUpRight size={18} />
          </button>
        </div>

        <div className="desk-source">
          <SourceView source={sources[0]} />
        </div>
      </Reveal>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Inspect the supporting source"
      >
        <SourceView source={sources[0]} />
        <p className="dialog-note">Sample source excerpt</p>
      </Dialog>
    </section>
  );
}

function JournalTeaser() {
  return (
    <section className="journal-teaser">
      <div className="journal-teaser-title">
        <h2>Build notes.</h2>
        <SectionLink href="/journal">Read the notes</SectionLink>
      </div>
      <Link
        className="journal-preview"
        href="/journal/evidence-before-confidence"
      >
        <div className="article-art art-evidence">
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
          <svg viewBox="0 0 300 180" fill="none" aria-hidden="true">
            <path
              d="M180 40Q260 30 230 130H120"
              stroke="#D84931"
              strokeWidth="1.3"
              strokeDasharray="4 4"
            />
          </svg>
        </div>

        <h3>Checking an answer against its sources.</h3>
        <p>
          Why an inspectable finding is more useful than a convincing paragraph.
        </p>
        <ArrowUpRight size={18} />
      </Link>
      <Link className="journal-preview" href="/journal/a-snapshot-is-a-promise">
        <div className="article-art art-version">
          <div className="art-version-card">
            v1<span>Active</span>
          </div>
          <span className="version-curve" />
          <div className="art-version-card second">
            v2<span>Staging</span>
          </div>
        </div>

        <h3>Keeping document versions together.</h3>
        <p>Keeping versions coherent when your sources keep changing.</p>
        <ArrowUpRight size={18} />
      </Link>
    </section>
  );
}

export function Landing() {
  return (
    <div className="landing" id="top">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <div className="site-container">
        <PublicNav />
        <main id="main">
          <section className="hero-new">
            <h1>
              Know what follows
              <br />
              <em>the change.</em>
            </h1>
            <div className="hero-intro">
              <p>
                See which services and integrations depend on an API change.
                <br className="desktop-only" /> Open the code and documents
                behind each finding.
              </p>
              <div>
                <Action href="/app">Get started</Action>
                <Link href="/app/investigations/INV-014" className="watch-link">
                  <Play size={12} fill="currentColor" />
                  Walk through an example
                </Link>
              </div>
            </div>
            <Reveal className="hero-scene-wrap">
              <ChangePreview />
            </Reveal>
          </section>

          <DependencyStory />
          <EvidenceDesk />
          <VersionDemo />
          <JournalTeaser />
          <section className="final-invitation">
            <h2>
              Try a change.
              <br />
              <em>Inspect the result.</em>
            </h2>
            <div className="invitation-bottom">
              <p>
                Choose a sample change and inspect its report.
                <br />
                No setup needed.
              </p>
              <Action href="/app">Open ImpactOS</Action>
            </div>
          </section>
        </main>
        <PublicFooter />
      </div>
    </div>
  );
}
