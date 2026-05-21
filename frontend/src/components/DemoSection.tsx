"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Boxes,
  GraduationCap,
  Loader2,
  Newspaper,
  Scale,
  Sparkles,
  Trash2,
  Users,
  Zap,
} from "lucide-react";

import { getDemoStatus, seedDemo, clearDemo, type DemoCounts, type DemoStatus } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";

const ENTITIES: { key: keyof DemoCounts; label: string; href: string; icon: typeof Zap }[] = [
  { key: "crises", label: "Crises", href: "/crisis", icon: AlertTriangle },
  { key: "signals", label: "Signals", href: "/signals", icon: Zap },
  { key: "stakeholders", label: "Stakeholders", href: "/stakeholders", icon: Users },
  { key: "resources", label: "Resources", href: "/resources", icon: Boxes },
  { key: "simulations", label: "Simulations", href: "/simulations", icon: GraduationCap },
  { key: "media_mentions", label: "Media", href: "/media", icon: Newspaper },
  { key: "legal_holds", label: "Legal Holds", href: "/legal-holds", icon: Scale },
];


export function DemoSection() {
  const { user, token, loading: authLoading } = useAuth();
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [busy, setBusy] = useState<"seed" | "clear" | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!token) return;
    setStatusLoading(true);
    try {
      setStatus(await getDemoStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load demo status");
    } finally {
      setStatusLoading(false);
    }
  }

  useEffect(() => {
    if (token) refresh();
  }, [token]);

  async function handleSeed() {
    setBusy("seed");
    setError(null);
    try {
      await seedDemo();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Seed failed");
    } finally {
      setBusy(null);
    }
  }

  async function handleClear() {
    if (!confirm("Remove all demo data? This cannot be undone (real data is untouched).")) return;
    setBusy("clear");
    setError(null);
    try {
      await clearDemo();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clear failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section id="demo" className="py-20 sm:py-24 bg-gradient-to-br from-pink-50 via-white to-rose-50">
      <div className="mx-auto max-w-5xl px-6">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-pink-600 text-white px-3 py-1 text-xs font-medium mb-3">
            <Sparkles className="h-3 w-3" />
            Try it live
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">See it in action</h2>
          <p className="mt-3 text-base text-gray-600 max-w-2xl mx-auto">
            One click loads a realistic incident-response dataset — two crises (one active, one resolved),
            a team roster, stakeholders, AI-scored signals, a media coverage feed, and more.
            Clear it any time.
          </p>
        </div>

        <div className="rounded-2xl border border-pink-200 bg-white shadow-lg p-6 sm:p-8">
          {authLoading ? (
            <div className="text-center text-sm text-gray-500 py-8">Loading…</div>
          ) : !user ? (
            <SignedOutCTA />
          ) : status === null ? (
            <div className="text-center text-sm text-gray-500 py-8">
              {statusLoading ? "Checking demo status…" : "—"}
            </div>
          ) : (
            <SignedInPanel
              status={status}
              busy={busy}
              statusLoading={statusLoading}
              onSeed={handleSeed}
              onClear={handleClear}
            />
          )}
          {error && (
            <div className="mt-4 text-sm bg-red-50 border border-red-200 text-red-700 rounded p-3">
              {error}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function SignedOutCTA() {
  return (
    <div className="text-center space-y-5 py-4">
      <p className="text-sm text-gray-700">
        Sign up (or sign in) to seed the demo dataset into your workspace.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link href="/signup?next=/#demo"><Button size="lg" className="bg-pink-600 hover:bg-pink-700">Create demo account</Button></Link>
        <Link href="/signin?next=/#demo"><Button size="lg" variant="outline">Sign in</Button></Link>
      </div>
      <p className="text-[11px] text-gray-500">
        Local stack — accounts and demo data live only in your own database.
      </p>
    </div>
  );
}

interface SignedInPanelProps {
  status: DemoStatus;
  busy: "seed" | "clear" | null;
  statusLoading: boolean;
  onSeed: () => void;
  onClear: () => void;
}

function SignedInPanel({ status, busy, statusLoading, onSeed, onClear }: SignedInPanelProps) {
  if (!status.seeded) {
    return (
      <div className="space-y-5">
        <div className="text-center space-y-3 py-4">
          <p className="text-sm text-gray-700">
            Workspace is empty (well, no demo data anyway). Click <strong>Seed demo data</strong> to
            load the dataset — it takes about a second and creates roughly 25 rows across 8 entity types.
          </p>
        </div>
        <div className="flex justify-center">
          <Button size="lg" onClick={onSeed} disabled={busy !== null} className="bg-pink-600 hover:bg-pink-700">
            {busy === "seed" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
            Seed demo data
          </Button>
        </div>
        <p className="text-center text-[11px] text-gray-500">
          Demo rows are prefixed with <code className="bg-slate-100 px-1 py-0.5 rounded">DEMO:</code> —
          clearing only removes those, never anything you've added yourself.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-sm text-gray-700">
          Demo data loaded. Jump into any of these and the AI Copilot is ready in the bottom-right of every page.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {ENTITIES.map(({ key, label, href, icon: Icon }) => {
          const count = status.counts[key];
          if (!count) return null;
          return (
            <Link
              key={key}
              href={href}
              className="group rounded-lg border border-slate-200 hover:border-pink-300 hover:shadow-sm transition p-3 bg-white"
            >
              <div className="flex items-center gap-2 text-pink-600">
                <Icon className="h-4 w-4" />
                <span className="text-2xl font-bold text-gray-900 tabular-nums">{count}</span>
              </div>
              <div className="mt-0.5 text-xs text-slate-600 group-hover:text-pink-700">{label}</div>
            </Link>
          );
        })}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2 border-t border-slate-100">
        <Link href="/dashboard">
          <Button size="lg" className="bg-pink-600 hover:bg-pink-700 w-full sm:w-auto">
            Open Command Center →
          </Button>
        </Link>
        <Button
          size="lg"
          variant="outline"
          onClick={onClear}
          disabled={busy !== null}
          className="text-red-700 border-red-200 hover:bg-red-50 hover:text-red-800"
        >
          {busy === "clear" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
          Clear demo data
        </Button>
      </div>

      {statusLoading && (
        <p className="text-center text-[11px] text-gray-400">Refreshing status…</p>
      )}
    </div>
  );
}
