"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Call, Candidate, Job } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

const statusVariant: Record<string, "default" | "secondary" | "success" | "warning" | "destructive"> = {
  queued: "secondary",
  in_progress: "warning",
  completed: "success",
  failed: "destructive",
};

function CandidateRow({ candidate }: { candidate: Candidate }) {
  const [calls, setCalls] = useState<Call[]>([]);
  const [calling, setCalling] = useState(false);

  const refresh = () => api.listCalls(candidate.id).then(setCalls).catch(() => {});

  useEffect(() => {
    refresh();
  }, [candidate.id]);

  async function onCall() {
    setCalling(true);
    try {
      await api.triggerCall(candidate.id);
      await refresh();
    } catch (e) {
      alert(String(e));
    } finally {
      setCalling(false);
    }
  }

  const latest = calls[calls.length - 1];

  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
      <div>
        <Link href={`/jobs/${candidate.job_id}/candidates/${candidate.id}`} className="font-medium hover:underline">
          {candidate.name}
        </Link>
        <p className="text-sm text-slate-500">{candidate.phone_number}</p>
      </div>
      <div className="flex items-center gap-3">
        {latest && <Badge variant={statusVariant[latest.status]}>{latest.status}</Badge>}
        <Button size="sm" variant="outline" onClick={onCall} disabled={calling}>
          {calling ? "Calling…" : "Call"}
        </Button>
      </div>
    </div>
  );
}

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [job, setJob] = useState<Job | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [adding, setAdding] = useState(false);

  const refreshCandidates = () => api.listCandidates(id).then(setCandidates).catch(() => {});

  useEffect(() => {
    api.getJob(id).then(setJob).catch(() => {});
    refreshCandidates();
  }, [id]);

  async function onAddCandidate(e: React.FormEvent) {
    e.preventDefault();
    setAdding(true);
    try {
      await api.addCandidate(id, { name, phone_number: phone });
      setName("");
      setPhone("");
      await refreshCandidates();
    } catch (err) {
      alert(String(err));
    } finally {
      setAdding(false);
    }
  }

  if (!job) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">{job.title}</h1>
        <p className="text-sm text-slate-500">{job.questions.length} screening question(s)</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Candidates</CardTitle>
        </CardHeader>
        <CardContent>
          {candidates.length === 0 && <p className="text-sm text-slate-500">No candidates yet.</p>}
          {candidates.map((c) => (
            <CandidateRow key={c.id} candidate={c} />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add candidate</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onAddCandidate} className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="phone">Phone number</Label>
              <Input
                id="phone"
                placeholder="+1..."
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={adding}>
              {adding ? "Adding…" : "Add"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
