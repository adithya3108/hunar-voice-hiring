import type { Call, Candidate, Job, JobKind, SearchJobResult } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listJobs: () => request<Job[]>("/jobs/"),
  getJob: (id: string) => request<Job>(`/jobs/${id}`),
  createJob: (payload: { title: string; kind: JobKind; description?: string; questions?: string[] }) =>
    request<Job>("/jobs/", { method: "POST", body: JSON.stringify(payload) }),

  listCandidates: (jobId: string) => request<Candidate[]>(`/jobs/${jobId}/candidates`),
  getCandidate: (id: string) => request<Candidate>(`/candidates/${id}`),
  addCandidate: (jobId: string, payload: { name: string; phone_number: string; email?: string }) =>
    request<Candidate>(`/jobs/${jobId}/candidates`, { method: "POST", body: JSON.stringify(payload) }),

  triggerCall: (candidateId: string) =>
    request<Call>(`/candidates/${candidateId}/call`, { method: "POST" }),
  listCalls: (candidateId: string) => request<Call[]>(`/candidates/${candidateId}/calls`),

  searchFromJD: (job_description: string, limit = 10) =>
    request<SearchJobResult>("/search/jobs", {
      method: "POST",
      body: JSON.stringify({ job_description, limit }),
    }),
  triggerReachout: (jobId: string, candidate_ids: string[]) =>
    request<Call[]>(`/search/jobs/${jobId}/reachout`, {
      method: "POST",
      body: JSON.stringify({ candidate_ids }),
    }),
};
