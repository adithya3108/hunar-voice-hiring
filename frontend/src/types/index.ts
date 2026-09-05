export type JobKind = "interview" | "reachout";

export interface Job {
  id: string;
  title: string;
  kind: JobKind;
  description: string;
  questions: string[];
  hunar_agent_id: string | null;
  created_at: string;
}

export interface Candidate {
  id: string;
  job_id: string;
  name: string;
  phone_number: string;
  email: string | null;
  source: string;
  created_at: string;
}

export type CallStatus = "queued" | "in_progress" | "completed" | "failed";

export interface Call {
  id: string;
  candidate_id: string;
  hunar_call_id: string | null;
  status: CallStatus;
  recording_url: string | null;
  transcript: string | null;
  structured_result: Record<string, unknown>;
  ai_summary: string | null;
  ai_score: {
    summary?: string;
    communication_score?: number;
    relevance_score?: number;
    confidence_score?: number;
    per_question?: { question: string; answer_summary: string }[];
  };
  created_at: string;
  updated_at: string;
}

export interface SearchJobResult {
  job_id: string;
  parsed: {
    title: string;
    skills: string[];
    seniority: string;
  };
  candidates_found: number;
}
