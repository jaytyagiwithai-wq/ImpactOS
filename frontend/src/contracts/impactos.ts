// Proposed frontend contracts. No network calls or backend implementation.
export type ID = string;
export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";
export type FindingKind =
  | "confirmed_dependency"
  | "possible_impact"
  | "unknown";
export type SourceLocation =
  | { kind: "lines"; start: number; end: number }
  | { kind: "page"; page: number }
  | { kind: "json_pointer"; pointer: string };

export interface Evidence {
  id: ID;
  documentId: ID;
  title: string;
  versionId: ID;
  snapshotId: ID;
  location: SourceLocation;
  excerpt: string;
  mediaType: string;
}

export interface DependencyNode {
  id: ID;
  label: string;
  kind: "service" | "endpoint" | "event" | "field" | "customer" | "document";
}

export interface DependencyEdge {
  id: ID;
  fromId: ID;
  toId: ID;
  relation: string;
  snapshotId: ID;
  evidenceIds: ID[];
}

export interface Finding {
  id: ID;
  entityId?: ID;
  title: string;
  kind: FindingKind;
  severity?: "low" | "medium" | "high";
  explanation: string;
  evidenceIds: ID[];
  pathEdgeIds: ID[];
  nextSteps: string[];
}

export interface ImpactReport {
  snapshotId: ID;
  completeness: "complete" | "partial";
  changeSummary: string;
  findings: Finding[];
  unknowns: string[];
  limitations: string[];
}

export interface Investigation {
  id: ID;
  projectId: ID;
  title: string;
  status: JobStatus;
  stage?: string;
  updatedAt: string;
  report?: ImpactReport;
  error?: { code: string; message: string; requestId: string };
}

export interface NewInvestigation {
  projectId: ID;
  baselineSnapshotId: ID;
  proposedVersionId: ID;
  question?: string;
}

export interface Page<T> {
  items: T[];
  nextCursor: string | null;
}

export interface ImpactOSClient {
  listInvestigations(
    filters: {
      projectId: ID;
      status?: JobStatus;
      query?: string;
      cursor?: string;
    },
    signal?: AbortSignal,
  ): Promise<Page<Investigation>>;
  createInvestigation(
    input: NewInvestigation,
    idempotencyKey: string,
  ): Promise<Investigation>;
  getInvestigation(id: ID, signal?: AbortSignal): Promise<Investigation>;
  getEvidence(id: ID, signal?: AbortSignal): Promise<Evidence>;
  getDependencies(
    input: { projectId: ID; snapshotId: ID; entityId: ID; depth: number },
    signal?: AbortSignal,
  ): Promise<{ nodes: DependencyNode[]; edges: DependencyEdge[] }>;
}
