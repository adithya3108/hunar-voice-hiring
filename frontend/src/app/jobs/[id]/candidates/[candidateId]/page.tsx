"use client";

import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Call, Candidate } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function CandidateDetailPage({
  params,
}: {
  params: Promise<{ id: string; candidateId: string }>;
}) {
  const { candidateId } = use(params);
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);

  useEffect(() => {
    api.getCandidate(candidateId).then(setCandidate).catch(() => {});
    const load = () => api.listCalls(candidateId).then(setCalls).catch(() => {});
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [candidateId]);

  if (!candidate) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">{candidate.name}</h1>
        <p className="text-sm text-slate-500">{candidate.phone_number}</p>
      </div>

      {calls.length === 0 && <p className="text-sm text-slate-500">No calls yet.</p>}

      {[...calls].reverse().map((call) => (
        <Card key={call.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Call · {new Date(call.created_at).toLocaleString()}</CardTitle>
              <Badge>{call.status}</Badge>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {call.recording_url && (
              <audio controls src={call.recording_url} className="w-full">
                Your browser does not support audio playback.
              </audio>
            )}

            {call.ai_score?.summary && (
              <div>
                <h3 className="text-sm font-semibold">AI summary</h3>
                <p className="text-sm text-slate-600">{call.ai_score.summary}</p>
                <div className="mt-2 flex gap-2">
                  {call.ai_score.communication_score !== undefined && (
                    <Badge variant="secondary">Communication: {call.ai_score.communication_score}/5</Badge>
                  )}
                  {call.ai_score.relevance_score !== undefined && (
                    <Badge variant="secondary">Relevance: {call.ai_score.relevance_score}/5</Badge>
                  )}
                  {call.ai_score.confidence_score !== undefined && (
                    <Badge variant="secondary">Confidence: {call.ai_score.confidence_score}/5</Badge>
                  )}
                </div>
              </div>
            )}

            {call.ai_score?.per_question && call.ai_score.per_question.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold">Question breakdown</h3>
                <ul className="mt-1 flex flex-col gap-2">
                  {call.ai_score.per_question.map((qa, i) => (
                    <li key={i} className="text-sm">
                      <p className="font-medium text-slate-700">{qa.question}</p>
                      <p className="text-slate-500">{qa.answer_summary}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {call.transcript && (
              <details>
                <summary className="cursor-pointer text-sm font-semibold">Full transcript</summary>
                <pre className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{call.transcript}</pre>
              </details>
            )}

            {Object.keys(call.structured_result ?? {}).length > 0 && (
              <details>
                <summary className="cursor-pointer text-sm font-semibold">Structured result (raw)</summary>
                <pre className="mt-2 overflow-x-auto text-xs text-slate-500">
                  {JSON.stringify(call.structured_result, null, 2)}
                </pre>
              </details>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
