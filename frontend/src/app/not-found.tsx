import Link from "next/link";
export default function NotFound() {
  return (
    <main className="not-found">
      <h1>This page isn&apos;t in the picture.</h1>
      <p>Check the address or return to the workspace.</p>
      <Link className="button button-solid" href="/app">
        Open workspace →
      </Link>
    </main>
  );
}
