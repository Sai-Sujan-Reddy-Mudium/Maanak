"use client";

import { useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";
import { isSupabaseConfigured } from "@/lib/config";
import { getRoleFromUser } from "@/lib/roles";
import { createClient } from "@/lib/supabase/client";
import type { UserRole } from "@/lib/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<UserRole>("citizen");
  const [loading, setLoading] = useState(true);
  const configured = isSupabaseConfigured();

  useEffect(() => {
    if (!configured) {
      setLoading(false);
      return;
    }

    const supabase = createClient();

    const applyUser = (next: User | null) => {
      setUser(next);
      setRole(getRoleFromUser(next));
    };

    supabase.auth.getUser().then(({ data }) => {
      applyUser(data.user);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      applyUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, [configured]);

  return { user, role, loading, configured };
}
