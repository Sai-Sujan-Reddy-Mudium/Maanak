import { Suspense } from "react";
import { BrandMark } from "@/components/brand-mark";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <div className="relative grid min-h-svh lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-primary lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,oklch(0.72_0.14_70/0.35),transparent_42%),radial-gradient(circle_at_80%_80%,oklch(0.55_0.1_250/0.45),transparent_40%)]" />
        <div className="relative z-10 flex flex-col justify-between p-10 text-primary-foreground">
          <BrandMark />
          <div className="max-w-md space-y-4">
            <p className="font-heading text-4xl leading-tight">
              Ask the standard.
              <br />
              Inspect the source.
            </p>
            <p className="text-sm/6 text-primary-foreground/75">
              MAANAK is an AI compliance assistant for Bureau of Indian Standards.
              Every answer is grounded in clauses, pages, and verified snippets.
            </p>
          </div>
          <p className="text-xs text-primary-foreground/60">
            Role-based access for citizens and manufacturers.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-8">
          <div className="lg:hidden">
            <BrandMark />
          </div>
          <div>
            <h1 className="font-heading text-3xl">Sign in</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Continue to the dual-pane RAG workspace.
            </p>
          </div>
          <Suspense fallback={<div className="h-48 animate-pulse rounded-xl bg-muted" />}>
            <LoginForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
