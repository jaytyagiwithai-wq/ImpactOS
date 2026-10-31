"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CircleHelp,
  FileCode2,
  FileText,
  GitBranch,
  LoaderCircle,
  Play,
  Pause,
  RotateCcw,
  X,
} from "lucide-react";
import { getSource } from "@/lib/demo";
import { Dialog, Mark } from "@/components/ui";
import { SourceView } from "@/components/source-view";

const findings = [
  {
    title: "Billing handler",
    detail: "Reads the removed field",
    source: "billing",
    icon: GitBranch,
  },
  {
    title: "Customer integration",
    detail: "Notice period needs review",
    source: "contract",
    icon: FileText,
  },
  {
    title: "Analytics worker",
    detail: "Handler source is missing",
    source: "catalog",
    icon: CircleHelp,
  },
];

type FlowGeometry = {
  width: number;
  height: number;
  hub: { x: number; y: number };
  trunk: string;
  branches: string[];
};

export function ChangePreview() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const [visible, setVisible] = useState(false);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [geometry, setGeometry] = useState<FlowGeometry | null>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const changeRef = useRef<HTMLDivElement>(null);
  const findingRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const reduce = useReducedMotion();
  const source = getSource(findings[active].source)!;

  useEffect(() => {
    const stage = stageRef.current;
    const change = changeRef.current;
    if (!stage || !change) return;
    let frame = 0;
    let disposed = false;
    const n = (value: number) => Math.round(value * 10) / 10;
    const measure = () => {
      const bounds = stage.getBoundingClientRect();
      const card = change.getBoundingClientRect();
      const targets = findingRefs.current.map((button) =>
        button?.getBoundingClientRect(),
      );
      if (
        !bounds.width ||
        targets.length !== findings.length ||
        targets.some((target) => !target)
      )
        return;
      const first = targets[0]!;
      const last = targets[2]!;
      const stacked = first.top >= card.bottom;
      const hub = stacked
        ? {
            x: n(card.left - bounds.left + card.width / 2),
            y: n(card.bottom - bounds.top + (first.top - card.bottom) / 2),
          }
        : {
            x: n((card.right + first.left) / 2 - bounds.left),
            y: n(
              (first.top + first.height / 2 + last.top + last.height / 2) / 2 -
                bounds.top,
            ),
          };
      const start = stacked
        ? { x: hub.x, y: n(card.bottom - bounds.top) }
        : {
            x: n(card.right - bounds.left),
            y: n(card.top - bounds.top + card.height / 2),
          };
      const trunk = stacked
        ? `M ${start.x} ${start.y} V ${hub.y}`
        : `M ${start.x} ${start.y} C ${(start.x + hub.x) / 2} ${start.y} ${(start.x + hub.x) / 2} ${hub.y} ${hub.x} ${hub.y}`;
      const branches = targets.map((target) => {
        const x = n(target!.left - bounds.left);
        const y = n(target!.top - bounds.top + target!.height / 2);
        if (stacked) {
          const bus = x - 18;
          const turn = hub.y + 20;
          const r = 9;
          return `V ${turn - r} Q ${hub.x} ${turn} ${hub.x - r} ${turn} H ${bus + r} Q ${bus} ${turn} ${bus} ${turn + r} V ${y - r} Q ${bus} ${y} ${bus + r} ${y} H ${x}`;
        }
        if (Math.abs(y - hub.y) < 1) return `H ${x}`;
        const direction = Math.sign(y - hub.y);
        const middle = n(hub.x + (x - hub.x) * 0.52);
        const r = n(Math.min(18, (x - hub.x) * 0.24, Math.abs(y - hub.y) / 2));
        return `H ${middle - r} Q ${middle} ${hub.y} ${middle} ${hub.y + direction * r} V ${y - direction * r} Q ${middle} ${y} ${middle + r} ${y} H ${x}`;
      });
      const next = {
        width: n(bounds.width),
        height: n(bounds.height),
        hub,
        trunk,
        branches,
      };
      setGeometry((previous) =>
        previous &&
        previous.width === next.width &&
        previous.height === next.height &&
        previous.trunk === trunk &&
        previous.branches.every((branch, i) => branch === branches[i])
          ? previous
          : next,
      );
    };
    const schedule = () => {
      if (disposed) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(measure);
    };
    const resize = new ResizeObserver(schedule);
    resize.observe(stage);
    resize.observe(change);
    findingRefs.current.forEach((button) => {
      if (button) resize.observe(button);
    });
    const intersection = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { threshold: 0.15 },
    );
    intersection.observe(stage);
    document.fonts.ready.then(() => {
      if (!disposed) schedule();
    });
    schedule();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resize.disconnect();
      intersection.disconnect();
    };
  }, []);

  const route = geometry
    ? `${geometry.trunk} ${geometry.branches[active]}`
    : "";
  return (
    <section
      className="change-preview connected-preview"
      id="investigate"
      aria-label="Explore the impact of an API change"
    >
      <div className="flow-stage" ref={stageRef}>
        {geometry && (
          <svg
            className="flow-connections"
            viewBox={`0 0 ${geometry.width} ${geometry.height}`}
            fill="none"
            aria-hidden="true"
          >
            <path className="flow-base" d={geometry.trunk} />
            {geometry.branches.map((branch, i) => (
              <path
                className="flow-base"
                key={i}
                d={`M ${geometry.hub.x} ${geometry.hub.y} ${branch}`}
              />
            ))}
            <motion.path
              key={active}
              className="flow-selected"
              d={route}
              initial={reduce ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            />
            {!reduce && (
              <path
                key={`packet-${active}`}
                className="flow-packet"
                d={route}
                pathLength={100}
                style={{
                  animationPlayState: paused || !visible ? "paused" : "running",
                }}
              />
            )}
          </svg>
        )}
        <div className="flow-board">
          <div className="flow-change-card" ref={changeRef}>
            <div className="flow-file-heading">
              <span>
                <FileCode2 size={17} />
                payment.yaml
              </span>
              <span>
                v2 <ArrowRight size={13} /> v3
              </span>
            </div>
            <div className="flow-change-heading">
              <h2>One field removed.</h2>
              <p>
                <code>payment.completed</code>
              </p>
            </div>
            <div className="flow-diff" aria-label="API schema diff">
              <div>
                <span>11</span>
                <code>properties:</code>
              </div>
              <div>
                <span>12</span>
                <code> payment_id: string</code>
              </div>
              <div className="flow-removed">
                <span>13</span>
                <code>− customer_id: string</code>
              </div>
              <div>
                <span>14</span>
                <code> amount: integer</code>
              </div>
            </div>
          </div>
          <div
            className="flow-findings"
            aria-label="Select an affected component"
          >
            {findings.map((finding, i) => (
              <button
                type="button"
                key={finding.source}
                ref={(el) => {
                  findingRefs.current[i] = el;
                }}
                onClick={() => setActive(i)}
                aria-pressed={active === i}
                aria-controls="flow-source"
                className={`flow-finding ${active === i ? "selected" : ""}`}
              >
                <span className={`flow-finding-icon flow-icon-${i}`}>
                  <finding.icon size={20} />
                </span>
                <span className="flow-finding-copy">
                  <strong>{finding.title}</strong>
                  <span>{finding.detail}</span>
                </span>
                <ArrowUpRight size={17} />
              </button>
            ))}
          </div>
        </div>
        {geometry && (
          <span
            className="flow-hub"
            style={{ left: geometry.hub.x, top: geometry.hub.y }}
            aria-hidden="true"
          >
            <Mark size={24} />
          </span>
        )}
      </div>
      <div className="flow-footer" id="flow-source">
        <button
          type="button"
          className="flow-source-button"
          onClick={() => setSourceOpen(true)}
          aria-label={`View source ${source.name}`}
        >
          <FileText size={16} />
          <span>{source.name}</span>
          <ArrowUpRight size={14} />
        </button>
        <div className="flow-footer-actions">
          {!reduce && (
            <button
              type="button"
              className="flow-toggle"
              onClick={() => setPaused(!paused)}
              aria-pressed={paused}
              aria-label={
                paused
                  ? "Resume connection animation"
                  : "Pause connection animation"
              }
            >
              {paused ? <Play size={14} /> : <Pause size={14} />}
              <span>{paused ? "Resume" : "Pause"}</span>
            </button>
          )}
          <Link href="/app/investigations/INV-014">
            Open report <ArrowUpRight size={15} />
          </Link>
        </div>
      </div>
      <Dialog
        open={sourceOpen}
        onClose={() => setSourceOpen(false)}
        title={source.name}
      >
        <SourceView source={source} />
      </Dialog>
    </section>
  );
}

const updateFiles = ["payment.yaml", "handlers.py", "service-agreement.md"];
type Outcome = "success" | "failure";

export function VersionDemo() {
  const [outcome, setOutcome] = useState<Outcome>("success");
  const [phase, setPhase] = useState(0);
  const [running, setRunning] = useState(false);
  const [run, setRun] = useState(0);
  const reduce = useReducedMotion();
  const failed = outcome === "failure" && phase >= 3;
  const switched = outcome === "success" && phase === 4;
  const ready = failed ? 1 : Math.max(0, Math.min(phase - 1, 3));
  const play = (nextOutcome = outcome) => {
    setOutcome(nextOutcome);
    setPhase(reduce ? 4 : 1);
    setRunning(!reduce);
    setRun((r) => r + 1);
  };
  useEffect(() => {
    if (!running) return;
    if (reduce) {
      setPhase(4);
      setRunning(false);
      return;
    }
    if (phase === 4 || failed) {
      setRunning(false);
      return;
    }
    const timer = window.setTimeout(
      () => setPhase((p) => Math.min(p + 1, 4)),
      950,
    );
    return () => window.clearTimeout(timer);
  }, [running, phase, failed, reduce, run]);
  const statusFor = (index: number) => {
    if (failed)
      return index === 0 ? "Ready" : index === 1 ? "Failed" : "Not processed";
    if (phase === 4 || index < phase - 1) return "Ready";
    if (running && index === phase - 1) return "Preparing";
    return "Waiting";
  };
  return (
    <section className="document-versions" id="versions">
      <div className="document-versions-heading">
        <h2>
          Update documents.
          <br />
          <em>Keep versions together.</em>
        </h2>
        <p>
          New files are prepared separately. Answers switch to the updated set
          only when every file is ready.
        </p>
      </div>
      <div className="document-update-demo">
        <div className="document-update-controls">
          <div className="update-outcome" aria-label="Choose an update outcome">
            <button
              onClick={() => play("success")}
              aria-pressed={outcome === "success"}
            >
              Successful update
            </button>
            <button
              onClick={() => play("failure")}
              aria-pressed={outcome === "failure"}
            >
              Failed update
            </button>
          </div>
          <button
            className="update-play"
            onClick={() => play()}
            disabled={running}
          >
            {phase === 0 ? <Play size={15} /> : <RotateCcw size={15} />}
            {phase === 0 ? "Play update" : running ? "Updating…" : "Replay"}
          </button>
        </div>
        <div className="document-update-grid">
          <div className="incoming-files">
            <div className="incoming-heading">
              <h3>
                New files <span>v3</span>
              </h3>
              <span>{ready} of 3 ready</span>
            </div>
            <div
              className="incoming-progress"
              role="progressbar"
              aria-label="Files prepared"
              aria-valuenow={ready}
              aria-valuemin={0}
              aria-valuemax={3}
            >
              <span style={{ width: `${(ready / 3) * 100}%` }} />
            </div>
            <div className="incoming-file-list">
              {updateFiles.map((name, i) => {
                const status = statusFor(i);
                return (
                  <div
                    className={`incoming-file file-${status.toLowerCase().replaceAll(" ", "-")}`}
                    key={name}
                  >
                    {i === 2 ? <FileText size={20} /> : <FileCode2 size={20} />}
                    <span>{name}</span>
                    <span className="incoming-file-status">
                      {status === "Ready" ? (
                        <Check size={15} />
                      ) : status === "Failed" ? (
                        <X size={15} />
                      ) : status === "Preparing" ? (
                        <LoaderCircle className="update-spinner" size={15} />
                      ) : null}
                      {status}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="answer-context">
            <div className="answer-context-heading">
              <h3>Used for answers</h3>
              <span className="context-live">
                <span /> Active
              </span>
            </div>
            <motion.div
              key={switched ? "v3" : "v2"}
              initial={!reduce && switched ? { opacity: 0, y: 5 } : false}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="active-version-number">
                <span>{switched ? "v3" : "v2"}</span>
                <span>{switched ? "Updated files" : "Current files"}</span>
              </div>
              <div className="answer-file-list">
                {updateFiles.map((name) => (
                  <div key={name}>
                    <span>{name}</span>
                    <span className={switched ? "version-updated" : ""}>
                      {switched ? "v3" : "v2"}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
        <div
          className={`document-update-message ${failed ? "update-failed" : ""}`}
        >
          {failed ? (
            <CircleHelp size={18} />
          ) : switched ? (
            <Check size={18} />
          ) : (
            <ArrowRight size={18} />
          )}
          <p>
            {failed
              ? "The update failed. Answers still use the complete v2 files."
              : switched
                ? "All three files are ready. Answers now use v3."
                : running
                  ? "Preparing the new files. Answers keep using v2 until everything is ready."
                  : "Play an update to see when the answer sources change."}
          </p>
        </div>
      </div>
    </section>
  );
}
