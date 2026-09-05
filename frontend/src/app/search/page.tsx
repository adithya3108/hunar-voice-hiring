"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Candidate, SearchJobResult } from "@/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function SearchPage() {
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchJobResult | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [reachingOut, setReachingOut] = useState(false);
  const [reachoutDone, setReachoutDone] = useState(false);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReachoutDone(false);
    try {
      const r = await api.searchFromJD(jd, 10);
      setResult(r);
      const cands = await api.listCandidates(r.job_id);
      setCandidates(cands);
      setSelected(new Set(cands.map((c) => c.id)));
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function onReachout() {
    if (!result) return;
    setReachingOut(true);
    try {
      await api.triggerReachout(result.job_id, Array.from(selected));
      setReachoutDone(true);
    } catch (err) {
      alert(String(err));
    } finally {
      setReachingOut(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">People search & reachout</h1>
        <p className="text-sm text-slate-500">
          Paste a job description — we&apos;ll find matching candidates via People Data Labs and reach out
          by voice.
        </p>
      </div>

      <Card>
        <CardContent className="pt-4">
          <form onSubmit={onSearch} className="flex flex-col gap-3">
            <Textarea
              rows={8}
              placeholder="Paste the full job description here…"
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              required
            />
            <Button type="submit" disabled={loading} className="self-start">
              {loading ? "Searching…" : "Find candidates"}
            </Button>
          </form>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>{result.parsed.title}</CardTitle>
            <CardDescription>
              {result.parsed.seniority} · {result.parsed.skills.join(", ")}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {candidates.length === 0 && (
              <p className="text-sm text-slate-500">No candidates with phone numbers found.</p>
            )}
            {candidates.map((c) => (
              <label key={c.id} className="flex items-center gap-3 border-b border-slate-100 py-2 last:border-0">
                <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggle(c.id)} />
                <div>
                  <p className="font-medium">{c.name}</p>
                  <p className="text-sm text-slate-500">{c.phone_number}</p>
                </div>
              </label>
            ))}
            {candidates.length > 0 && (
              <Button onClick={onReachout} disabled={reachingOut || selected.size === 0} className="self-start">
                {reachingOut ? "Calling…" : `Call ${selected.size} candidate(s)`}
              </Button>
            )}
            {reachoutDone && (
              <p className="text-sm text-emerald-700">
                Reachout calls started.{" "}
                <Link href={`/jobs/${result.job_id}`} className="underline">
                  View progress <Badge variant="secondary">job dashboard</Badge>
                </Link>
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
