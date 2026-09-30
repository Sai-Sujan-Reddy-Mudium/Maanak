"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { fetchMetrics } from "@/lib/sse";
import type { RagMetrics } from "@/lib/types";

function MetricRing({ label, value }: { label: string; value: number }) {
  const clamped = Math.min(Math.max(value, 0), 1);
  const percent = Math.round(clamped * 100);
  const radius = 34;
  const circ = 2 * Math.PI * radius;
  const offset = circ - clamped * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg viewBox="0 0 88 88" className="size-24">
        <circle
          cx="44"
          cy="44"
          r={radius}
          className="stroke-muted fill-none"
          strokeWidth="8"
        />
        <circle
          cx="44"
          cy="44"
          r={radius}
          className="fill-none stroke-primary"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 44 44)"
        />
        <text
          x="44"
          y="48"
          textAnchor="middle"
          className="fill-foreground text-[16px] font-medium"
        >
          {percent}%
        </text>
      </svg>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function normalizeMetrics(raw: RagMetrics) {
  const faithfulness = Number(raw.faithfulness ?? raw.Faithfulness ?? 0);
  const precision = Number(
    raw.context_precision ?? raw.contextPrecision ?? raw["Context Precision"] ?? 0,
  );
  const latency = Number(raw.latency_ms ?? raw.latency ?? raw.Latency ?? 0);
  return { faithfulness, precision, latency };
}

export function MetricsDrawer() {
  const [open, setOpen] = useState(false);
  const [metrics, setMetrics] = useState<ReturnType<typeof normalizeMetrics> | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    fetchMetrics()
      .then((data) => setMetrics(normalizeMetrics(data)))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Unable to load metrics."),
      )
      .finally(() => setLoading(false));
  }, [open]);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button variant="ghost" size="icon-sm" aria-label="System health metrics" />
        }
      >
        <Activity />
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>System health</SheetTitle>
          <SheetDescription>
            Live RAGAS evaluation for the MAANAK retrieval pipeline.
          </SheetDescription>
        </SheetHeader>
        <div className="space-y-6 px-4 pb-6">
          {loading ? <p className="text-sm text-muted-foreground">Loading metrics…</p> : null}
          {error ? (
            <p className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </p>
          ) : null}
          {metrics ? (
            <>
              <div className="flex justify-around">
                <MetricRing label="Faithfulness" value={metrics.faithfulness} />
                <MetricRing label="Context precision" value={metrics.precision} />
              </div>
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { name: "Faithfulness", value: metrics.faithfulness * 100 },
                      { name: "Precision", value: metrics.precision * 100 },
                      {
                        name: "Latency",
                        value: Math.min(metrics.latency / 10, 100),
                      },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="var(--primary)" radius={6} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-sm text-muted-foreground">
                Median latency:{" "}
                <span className="font-medium text-foreground">
                  {Math.round(metrics.latency)} ms
                </span>
              </p>
            </>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  );
}
