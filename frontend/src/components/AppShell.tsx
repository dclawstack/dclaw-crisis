"use client";

import { usePathname } from "next/navigation";

import { AppSidebar } from "@/components/AppSidebar";
import { useAuth } from "@/lib/auth";

const NO_SHELL_PATHS = new Set(["/", "/signin", "/signup"]);

/**
 * Wraps authenticated pages with a fixed left sidebar + main content area.
 * Skips the landing page, signin, and signup so they stay full-bleed.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { token, loading } = useAuth();

  // Public pages render bare; AuthGuard handles redirects elsewhere.
  if (!pathname || NO_SHELL_PATHS.has(pathname)) {
    return <>{children}</>;
  }
  // While we're still figuring out whether the user is signed in, render
  // the children alone (no sidebar flash) — AuthGuard handles redirect.
  if (loading || !token) {
    return <>{children}</>;
  }
  return (
    <div className="min-h-screen bg-gray-50">
      <AppSidebar />
      <div className="lg:pl-60">
        {children}
      </div>
    </div>
  );
}
