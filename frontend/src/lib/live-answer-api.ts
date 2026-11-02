export type LiveCitation = {
  evidence_id: number;
  chunk_id: string;
  document_title: string;
  version_number: number;
  chunk_index: number;
};

export type LiveAnswer = {
  ranking_mode: "reranked" | "rrf_fallback";
  status: "answered" | "insufficient_evidence";
  answer: string;
  citations: LiveCitation[];
  unknowns: string[];
};

export type SourceType = "text" | "markdown" | "code" | "openapi";

export type DocumentVersion = {
  id: string;
  document_id: string;
  version_number: number;
  original_filename: string;
  media_type: string;
  sha256: string;
  byte_size: number;
  status: "uploaded" | "processing" | "ready" | "failed";
  created_at: string;
};

export type SourceRecord = {
  document: {
    id: string;
    title: string;
    source_type: SourceType;
    status: string;
    created_at: string;
  };
  latest_version: DocumentVersion | null;
};

export type SourceChunk = {
  chunk_id: string;
  document_id: string;
  document_title: string;
  source_type: SourceType;
  version_id: string;
  version_number: number;
  original_filename: string;
  chunk_index: number;
  content: string;
};

const origin = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(new URL(path, origin), {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(
      typeof payload?.detail === "string"
        ? payload.detail
        : `The API request failed (${response.status}).`,
    );
  }
  return response.json() as Promise<T>;
}

export function askEvidence(queryText: string, signal?: AbortSignal) {
  return api<LiveAnswer>("/v1/answers", {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query_text: queryText }),
  });
}

export function listSources() { return api<SourceRecord[]>("/v1/documents"); }
export function getSourceChunk(chunkId: string) { return api<SourceChunk>(`/v1/documents/chunks/${chunkId}`); }

export async function uploadAndIndexSource(input: {
  title: string;
  sourceType: SourceType;
  file: File;
  onVersion?: (version: DocumentVersion) => void;
}): Promise<DocumentVersion> {
  const document = await api<{ id: string }>("/v1/documents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: input.title, source_type: input.sourceType }),
  });
  const form = new FormData();
  form.append("file", input.file);
  const uploaded = await api<DocumentVersion>(`/v1/documents/${document.id}/versions`, { method: "POST", body: form });
  input.onVersion?.(uploaded);
  return api<DocumentVersion>(`/v1/documents/${document.id}/versions/${uploaded.id}/index`, { method: "POST" });
}

export function inferSourceType(filename: string): SourceType {
  const extension = filename.split(".").pop()?.toLowerCase();
  if (["py", "ts", "tsx", "js", "jsx", "java", "go", "sql", "rb", "cs"].includes(extension ?? "")) return "code";
  if (["yaml", "yml", "json"].includes(extension ?? "")) return "openapi";
  if (["md", "mdx"].includes(extension ?? "")) return "markdown";
  return "text";
}
