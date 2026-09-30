import { Suspense } from "react";
import { BrandMark } from "@/components/brand-mark";
import { SignupForm } from "@/components/auth/signup-form";

export default function SignupPage() {
  return (
    <div className="relative grid min-h-svh lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-primary lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_10%,oklch(0.72_0.14_70/0.4),transparent_38%)]" />
        <div className="relative z-10 flex flex-col justify-between p-10 text-primary-foreground">
          <BrandMark />
          <div className="max-w-md space-y-6">
            <p className="font-heading text-4xl leading-tight">Choose your access.</p>
            <ul className="space-y-3 text-sm text-primary-foreground/80">
              <li>
                <span className="font-medium text-primary-foreground">Citizen</span>
                {" — "}ask IS clauses and inspect citations.
              </li>
              <li>
                <span className="font-medium text-primary-foreground">Manufacturer</span>
                {" — "}look up labs, schemes, and product standards.
              </li>
            </ul>
          </div>
          <p className="text-xs text-primary-foreground/60">
            Your role is stored in Supabase user metadata and enforced in middleware.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-8">
          <div className="lg:hidden">
            <BrandMark />
          </div>
          <div>
            <h1 className="font-heading text-3xl">Create account</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Email, password, and a mandatory role.
            </p>
          </div>
          <Suspense fallback={<div className="h-48 animate-pulse rounded-xl bg-muted" />}>
            <SignupForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
