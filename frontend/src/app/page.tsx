"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Job } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listJobs()
      .then(setJobs)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Jobs</h1>
          <p className="text-sm text-slate-500">
            Screening interviews run by your Hunar.AI voice agent.
          </p>
        </div>
        <Link href="/jobs/new">
          <Button>New job</Button>
        </Link>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {!loading && !error && jobs.length === 0 && (
        <p className="text-sm text-slate-500">No jobs yet. Create one to get started.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {jobs.map((job) => (
          <Link key={job.id} href={`/jobs/${job.id}`}>
            <Card className="h-full transition-shadow hover:shadow-md">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{job.title}</CardTitle>
                  <Badge variant={job.kind === "interview" ? "default" : "secondary"}>{job.kind}</Badge>
                </div>
                <CardDescription>{job.questions.length} screening question(s)</CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-slate-500">
                Created {new Date(job.created_at).toLocaleDateString()}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
