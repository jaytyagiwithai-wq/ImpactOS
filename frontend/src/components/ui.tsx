"use client";
import Link from "next/link";
import { ArrowUpRight, X, ArrowRight } from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";

export function Mark({ size = 30 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M3 14H12L22 4H32V12H26L20 18L26 24H32V32H22L12 22H3Z"
        fill="currentColor"
      />
    </svg>
  );
}
export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link className="brand" href={href} aria-label="ImpactOS home">
      <Mark />
      <span>
        impact<span className="brand-os">os</span>
      </span>
    </Link>
  );
}
export function Action({
  href,
  children,
  secondary = false,
  className = "",
}: {
  href: string;
  children: ReactNode;
  secondary?: boolean;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={`button ${secondary ? "button-outline" : "button-solid"} ${className}`}
    >
      {children}
      <ArrowUpRight size={16} />
    </Link>
  );
}
export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="eyebrow">
      <span />
      {children}
    </span>
  );
}
export function SectionLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link className="section-link" href={href}>
      {children}
      <ArrowRight size={18} />
    </Link>
  );
}
export function Badge({
  kind,
  children,
}: {
  kind: string;
  children: ReactNode;
}) {
  return <span className={`badge badge-${kind}`}>{children}</span>;
}
export function Dialog({
  open,
  onClose,
  title,
  children,
  sheet = false,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  sheet?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (open && !d?.open) d?.showModal();
    else if (!open && d?.open) d.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      onClose={onClose}
      className={`dialog ${sheet ? "source-sheet" : ""}`}
      aria-label={title}
    >
      <header>
        <h2>{title}</h2>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={18} />
        </button>
      </header>
      <div className="dialog-content">{children}</div>
    </dialog>
  );
}
