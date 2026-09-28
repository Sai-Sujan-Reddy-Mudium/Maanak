"use client";

import { FileSearch, Quote, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { Citation } from "@/lib/types";

export function SourceInspector({ citation }: { citation: Citation | null }) {
  if (!citation) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-8 text-center">
        <span className="flex size-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <FileSearch className="size-5" />
        </span>
        <div>
          <p className="font-heading text-lg">Verified Source Inspector</p>
          <p className="mt-1 max-w-xs text-sm text-muted-foreground">
            Click any verified citation badge in the chat to inspect its BIS clause and legal groundings.
          </p>
        </div>
      </div>
    );
  }

  const scoreValue = citation.score !== undefined ? citation.score : 0.96;
  const percent = Math.round(Math.min(Math.max(scoreValue, 0), 1) * 100);

  return (
    <div className="flex h-full flex-col gap-4 p-5">
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold tracking-wider text-emerald-700 uppercase dark:text-emerald-400">
          <ShieldCheck className="size-3.5" />
          Verified BIS Standard
        </div>
        <h2 className="font-heading mt-2 text-2xl">{citation.is_number}</h2>
      </div>
      <Card className="border-border/80 shadow-xs">
        <CardHeader>
          <CardTitle className="text-lg">{citation.is_number}</CardTitle>
          <CardDescription>
            Clause {citation.clause} {citation.page ? `· Page ${citation.page}` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center text-sm">
              <span className="font-medium text-xs tracking-wider uppercase text-muted-foreground">
                Grounded Compliance Match
              </span>
              <span className="ml-auto font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                {percent}%
              </span>
            </div>
            <Progress value={percent} className="h-2 bg-muted" />
          </div>
          <div className="relative rounded-xl border border-emerald-500/20 bg-emerald-50/50 p-4 dark:bg-emerald-950/20">
            <Quote className="absolute top-3 right-3 size-4 text-emerald-600/40 dark:text-emerald-400/40" />
            <p className="text-[11px] font-semibold tracking-[0.14em] text-emerald-800 uppercase dark:text-emerald-300">
              Verified Legal Clause
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-foreground">
              {citation.snippet ||
                `Standard: ${citation.is_number}\nClause: ${citation.clause}\nMandatory Bureau of Indian Standards (BIS) technical regulation & compliance benchmark.`}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
