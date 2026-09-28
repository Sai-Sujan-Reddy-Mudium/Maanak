import Link from "next/link";
import { ShieldAlert } from "lucide-react";
import { BrandMark } from "@/components/brand-mark";
import { buttonVariants } from "@/components/ui/button";

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6">
      <BrandMark />
      <div className="max-w-md space-y-4 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <ShieldAlert className="size-6" />
        </div>
        <h1 className="font-heading text-3xl">Access restricted</h1>
        <p className="text-sm text-muted-foreground">
          This route is reserved for auditors. Your current role cannot open the
          auditor dashboard or live RAGAS metrics.
        </p>
        <Link href="/chat" className={buttonVariants({ variant: "default" })}>
          Return to chat
        </Link>
      </div>
    </div>
  );
}
