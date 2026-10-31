import { WorkspaceShell } from "@/components/workspace-shell";
import "./demo.css";
export const metadata = { title: "Try ImpactOS" };
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}
