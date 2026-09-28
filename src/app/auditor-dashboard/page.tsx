"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BrandMark } from "@/components/brand-mark";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchMetrics } from "@/lib/sse";

type Normalized = {
  faithfulness: number;
  precision: number;
  latency: number;
};

function normalize(raw: Record<string, number>): Normalized {
  return {
    faithfulness: Number(raw.faithfulness ?? 0),
    precision: Number(raw.context_precision ?? raw.contextPrecision ?? 0),
    latency: Number(raw.latency_ms ?? raw.latency ?? 0),
  };
}

export default function AuditorDashboardPage() {
  const [metrics, setMetrics] = useState<Normalized | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics()
      .then((data) => setMetrics(normalize(data)))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Unable to load metrics."),
      );
  }, []);

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <BrandMark compact />
        <Link
          href="/chat"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Back to chat
        </Link>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 space-y-6 p-6">
        <div>
          <p className="text-[11px] tracking-[0.18em] text-muted-foreground uppercase">
            Auditor only
          </p>
          <h1 className="font-heading text-3xl">RAGAS system health</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Faithfulness, context precision, and latency from GET /api/v1/metrics.
          </p>
        </div>
        {error ? (
          <p className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </p>
        ) : null}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardDescription>Faithfulness</CardDescription>
              <CardTitle className="text-3xl">
                {metrics ? `${Math.round(metrics.faithfulness * 100)}%` : "—"}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Context precision</CardDescription>
              <CardTitle className="text-3xl">
                {metrics ? `${Math.round(metrics.precision * 100)}%` : "—"}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Latency</CardDescription>
              <CardTitle className="text-3xl">
                {metrics ? `${Math.round(metrics.latency)} ms` : "—"}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Evaluation snapshot</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            {metrics ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { name: "Faithfulness", value: metrics.faithfulness * 100 },
                    { name: "Precision", value: metrics.precision * 100 },
                    { name: "Latency (ms/10)", value: Math.min(metrics.latency / 10, 100) },
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="var(--primary)" radius={8} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground">Waiting for metrics…</p>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
