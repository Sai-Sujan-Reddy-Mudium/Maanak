"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Search, MapPin, ExternalLink } from "lucide-react";
import { BrandMark } from "@/components/brand-mark";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { fetchLabs } from "@/lib/sse";
import type { LabRecord } from "@/lib/types";

export default function LabsPage() {
  const { role } = useAuth();
  const [query, setQuery] = useState("");
  const [labs, setLabs] = useState<LabRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function onSearch(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data = await fetchLabs(query.trim(), role);
      setLabs(Array.isArray(data) ? data : []);
    } catch (err) {
      setLabs([]);
      setError(err instanceof Error ? err.message : "Unable to load labs.");
    } finally {
      setLoading(false);
    }
  }

  const count = useMemo(() => labs.length, [labs]);

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
            Directory
          </p>
          <h1 className="font-heading text-3xl">Recognized BIS labs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Search by IS code to find labs certified for that standard.
          </p>
        </div>
        <form onSubmit={onSearch} className="flex gap-2">
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search IS code — e.g. IS 1293"
            className="h-10"
          />
          <Button type="submit" className="h-10" disabled={loading}>
            <Search />
            {loading ? "Searching…" : "Search"}
          </Button>
        </form>
        {error ? (
          <p className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </p>
        ) : null}
        {searched && !error ? (
          <p className="text-sm text-muted-foreground">{count} lab{count === 1 ? "" : "s"} found</p>
        ) : null}
        <div className="rounded-xl ring-1 ring-foreground/10">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lab name</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Map</TableHead>
                <TableHead>Scope</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {labs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="py-10 text-center text-muted-foreground">
                    {searched
                      ? "No labs matched this IS code."
                      : "Enter an IS code and search the directory."}
                  </TableCell>
                </TableRow>
              ) : (
                labs.map((lab) => {
                  const mapUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${lab.lab_name}, ${lab.location}`)}`;
                  return (
                    <TableRow key={`${lab.lab_name}-${lab.location}`}>
                      <TableCell className="font-medium whitespace-normal">{lab.lab_name}</TableCell>
                      <TableCell className="whitespace-normal">{lab.location}</TableCell>
                      <TableCell className="whitespace-nowrap">
                        <a 
                          href={mapUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-800 hover:underline text-sm font-medium"
                        >
                          <MapPin className="size-4" />
                          View Map
                        </a>
                      </TableCell>
                      <TableCell className="whitespace-normal">
                        <div className="flex flex-wrap gap-1">
                          {(lab.scope ?? []).map((item) => (
                            <Badge key={item} variant="secondary">
                              {item}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </main>
    </div>
  );
}
