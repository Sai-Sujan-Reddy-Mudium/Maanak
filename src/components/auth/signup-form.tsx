"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GoogleIcon } from "@/components/icons/google-icon";
import { isSupabaseConfigured } from "@/lib/config";
import { roleLabel } from "@/lib/roles";
import { createClient } from "@/lib/supabase/client";
import { USER_ROLES, type UserRole } from "@/lib/types";

export function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("citizen");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [googlePending, setGooglePending] = useState(false);

  useEffect(() => {
    const err = searchParams.get("error");
    if (err === "oauth_failed") {
      setError("Google sign up was unsuccessful. Please try again.");
    }
  }, [searchParams]);

  async function onGoogleSignUp() {
    setError(null);
    setMessage(null);

    if (!isSupabaseConfigured()) {
      setError(
        "Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to .env.local.",
      );
      return;
    }

    setGooglePending(true);
    try {
      const supabase = createClient();
      const callbackUrl = new URL("/auth/callback", window.location.origin);
      callbackUrl.searchParams.set("role", role);
      callbackUrl.searchParams.set("next", "/chat");

      const { error: oAuthError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: callbackUrl.toString(),
          queryParams: {
            access_type: "offline",
            prompt: "consent",
          },
        },
      });

      if (oAuthError) {
        setError(oAuthError.message);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to sign up with Google.",
      );
    } finally {
      setGooglePending(false);
    }
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (!isSupabaseConfigured()) {
      setError(
        "Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to .env.local.",
      );
      return;
    }

    setPending(true);
    try {
      const supabase = createClient();
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { role },
        },
      });
      if (signUpError) {
        setError(signUpError.message);
        return;
      }
      if (data.session) {
        router.replace("/chat");
        router.refresh();
        return;
      }
      setMessage(
        "Account created. Check your email to confirm, then sign in. Your role is stored in user metadata.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign up.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="role">Role</Label>
        <Select
          value={role}
          onValueChange={(value) => {
            if (value) setRole(value as UserRole);
          }}
        >
          <SelectTrigger id="role" className="h-10 w-full">
            <SelectValue placeholder="Select your access role" />
          </SelectTrigger>
          <SelectContent>
            {USER_ROLES.map((item) => (
              <SelectItem key={item} value={item}>
                {roleLabel(item)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          This role is saved to your account metadata and used for RBAC.
        </p>
      </div>

      <Button
        type="button"
        variant="outline"
        className="h-10 w-full gap-2 border-border font-medium shadow-xs hover:bg-accent"
        onClick={onGoogleSignUp}
        disabled={pending || googlePending}
      >
        <GoogleIcon className="size-4" />
        {googlePending ? "Redirecting to Google…" : "Sign up with Google"}
      </Button>

      <div className="relative my-2 flex items-center justify-center">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <span className="relative bg-background px-2 text-xs uppercase tracking-wider text-muted-foreground">
          or continue with email
        </span>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@organisation.in"
            className="h-10"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="At least 8 characters"
            className="h-10"
          />
        </div>

        {error ? (
          <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}
        {message ? (
          <p className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm">
            {message}
          </p>
        ) : null}
        <Button
          type="submit"
          className="h-10 w-full"
          disabled={pending || googlePending}
        >
          {pending ? "Creating account…" : "Create account"}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already registered?{" "}
          <Link
            href="/login"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
