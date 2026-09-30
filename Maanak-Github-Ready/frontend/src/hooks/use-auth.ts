"use client";

import { useEffect, useState } from "react";
import type { UserRole } from "@/lib/types";
import { useRouter, usePathname } from "next/navigation";

export function useAuth() {
  const [user, setUser] = useState<any>(null);
  const [role, setRole] = useState<UserRole>("citizen");
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkAuth = () => {
      const auth = localStorage.getItem("maanak_auth");
      if (auth === "admin_logged_in") {
        setUser({ id: "admin-user", email: "admin" });
      } else {
        setUser(null);
        if (pathname !== "/login") {
            router.push("/login");
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, [pathname, router]);

  return { user, role, loading, configured: true };
}
