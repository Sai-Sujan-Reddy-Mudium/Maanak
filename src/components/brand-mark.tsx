import Link from "next/link";
import { Scale } from "lucide-react";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/chat" className="flex items-center gap-2.5">
      <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
        <Scale className="size-4" />
      </span>
      <span className="leading-tight">
        <span className="font-heading block text-lg tracking-tight">MAANAK</span>
        {!compact ? (
          <span className="block text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
            BIS compliance
          </span>
        ) : null}
      </span>
    </Link>
  );
}
