"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";

const PUBLIC_PATHS = new Set(["/", "/signin", "/signup"]);

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, loading } = useAuth();

  const isPublic = !pathname || PUBLIC_PATHS.has(pathname);

  useEffect(() => {
    if (loading) return;
    if (!isPublic && !token) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/signin${next}`);
    }
  }, [loading, token, isPublic, pathname, router]);

  if (loading && !isPublic) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-slate-500">
        Checking session…
      </div>
    );
  }
  if (!isPublic && !token) {
    return null;
  }
  return <>{children}</>;
}
