"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  Boxes,
  CheckSquare,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Newspaper,
  Scale,
  ScrollText,
  Users,
  UserCog,
  X,
  Zap,
} from "lucide-react";

import { useAuth, clearSession } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: typeof Activity;
}

const NAV_GROUPS: { heading?: string; items: NavItem[] }[] = [
  {
    items: [
      { label: "Command Center", href: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    heading: "Detection",
    items: [
      { label: "Signals", href: "/signals", icon: Zap },
    ],
  },
  {
    heading: "Response",
    items: [
      { label: "Crises", href: "/crisis", icon: AlertTriangle },
      { label: "Action Items", href: "/action-items", icon: CheckSquare },
      { label: "Playbooks", href: "/playbooks", icon: ScrollText },
    ],
  },
  {
    heading: "People & resources",
    items: [
      { label: "Team", href: "/team", icon: UserCog },
      { label: "Stakeholders", href: "/stakeholders", icon: Users },
      { label: "Resources", href: "/resources", icon: Boxes },
    ],
  },
  {
    heading: "After action",
    items: [
      { label: "Simulations", href: "/simulations", icon: GraduationCap },
      { label: "Media", href: "/media", icon: Newspaper },
      { label: "Legal Holds", href: "/legal-holds", icon: Scale },
    ],
  },
];

function isActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === "/dashboard") return pathname === "/dashboard";
  return pathname === href || pathname.startsWith(href + "/");
}

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  function handleSignOut() {
    clearSession();
    router.replace("/signin");
  }

  return (
    <>
      {/* Mobile top-bar with hamburger */}
      <div className="lg:hidden sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
        <Link href="/dashboard" className="flex items-center gap-2 text-pink-600 font-semibold">
          <Activity className="h-5 w-5" />
          DClaw Crisis
        </Link>
        <button
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
          className="rounded-md p-1.5 hover:bg-slate-100"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {/* Backdrop (mobile) */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      <aside
        className={cn(
          "fixed z-40 inset-y-0 left-0 w-60 flex-col bg-white border-r border-slate-200",
          "transform transition-transform duration-200 ease-out",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "lg:translate-x-0 lg:flex"
        )}
      >
        <div className="flex h-16 items-center justify-between px-5 border-b border-slate-200">
          <Link href="/dashboard" className="flex items-center gap-2 text-pink-600 font-semibold" onClick={() => setMobileOpen(false)}>
            <Activity className="h-5 w-5" />
            DClaw Crisis
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
            className="lg:hidden rounded-md p-1 hover:bg-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-4">
          {NAV_GROUPS.map((group, gi) => (
            <div key={gi}>
              {group.heading && (
                <div className="px-2 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  {group.heading}
                </div>
              )}
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(pathname, item.href);
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                        className={cn(
                          "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition",
                          active
                            ? "bg-pink-50 text-pink-700 font-medium"
                            : "text-slate-700 hover:bg-slate-100"
                        )}
                      >
                        <Icon className={cn("h-4 w-4 shrink-0", active && "text-pink-600")} />
                        <span>{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-slate-200 p-3">
          {user ? (
            <div className="flex items-center gap-2 rounded-md px-2 py-2 hover:bg-slate-100">
              <div className="h-7 w-7 rounded-full bg-pink-600 text-white flex items-center justify-center text-xs font-semibold shrink-0">
                {(user.name || user.email).slice(0, 1).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0 text-xs">
                <div className="truncate font-medium text-slate-800">{user.name || user.email}</div>
                {user.name && <div className="truncate text-slate-500">{user.email}</div>}
              </div>
              <button
                onClick={handleSignOut}
                aria-label="Sign out"
                className="rounded p-1 text-slate-500 hover:bg-slate-200 hover:text-slate-800"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/signin"
              className="block text-center text-sm rounded-md bg-pink-600 px-3 py-2 text-white hover:bg-pink-700"
            >
              Sign in
            </Link>
          )}
        </div>
      </aside>
    </>
  );
}
