import type {
  ImpactOSClient,
  NewInvestigation,
  Investigation as APIInvestigation,
  Evidence,
} from "@/contracts/impactos";

// Integration boundary for your FastAPI service. Demo views are explicitly isolated.
const origin = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(new URL(path, origin), {
    credentials: "include",
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => null);
    throw new Error(error?.error?.message || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}
export const httpClient: ImpactOSClient = {
  listInvestigations(filters, signal) {
    const params = new URLSearchParams({ project_id: filters.projectId });
    if (filters.status) params.set("status", filters.status);
    if (filters.query) params.set("q", filters.query);
    if (filters.cursor) params.set("cursor", filters.cursor);
    return request(`/v1/investigations?${params}`, { signal });
  },
  createInvestigation(input: NewInvestigation, idempotencyKey: string) {
    return request<APIInvestigation>("/v1/investigations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(input),
    });
  },
  getInvestigation(id, signal) {
    return request<APIInvestigation>(
      `/v1/investigations/${encodeURIComponent(id)}`,
      { signal },
    );
  },
  getEvidence(id, signal) {
    return request<Evidence>(`/v1/evidence/${encodeURIComponent(id)}`, {
      signal,
    });
  },
  getDependencies(input, signal) {
    const params = new URLSearchParams({
      project_id: input.projectId,
      snapshot_id: input.snapshotId,
      entity_id: input.entityId,
      depth: String(input.depth),
    });
    return request(`/v1/dependencies?${params}`, { signal });
  },
};
