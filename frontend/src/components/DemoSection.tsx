"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  Boxes,
  Copy,
  GraduationCap,
  Loader2,
  Newspaper,
  Scale,
  Sparkles,
  Trash2,
  Users,
  Zap,
} from "lucide-react";

import {
  getDemoStatus,
  seedDemo,
  resetDemo,
  signin,
  type DemoStatus,
  type DemoCredentials,
  type DemoCounts,
} from "@/lib/api";
import { setSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";

const ENTITIES: { key: keyof DemoCounts; label: string }[] = [
  { key: "crises", label: "Crises" },
  { key: "signals", label: "Signals" },
  { key: "stakeholders", label: "Stakeholders" },
  { key: "resources", label: "Resources" },
  { key: "simulations", label: "Simulations" },
  { key: "media_mentions", label: "Media mentions" },
  { key: "legal_holds", label: "Legal holds" },
  { key: "team_members", label: "Team members" },
];

const ENTITY_ICON: Record<string, typeof Zap> = {
  crises: AlertTriangle,
  signals: Zap,
  stakeholders: Users,
  resources: Boxes,
  simulations: GraduationCap,
  media_mentions: Newspaper,
  legal_holds: Scale,
  team_members: Users,
};


export function DemoSection() {
  const router = useRouter();
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [credentials, setCredentials] = useState<DemoCredentials | null>(null);
  const [probed, setProbed] = useState(false);
  const [busy, setBusy] = useState<"seed" | "reset" | "signin" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshStatus() {
    try {
      const s = await getDemoStatus();
      setStatus(s);
    } catch (e) {
      // Backend may not be reachable yet — keep the section hidden.
      setStatus(null);
    } finally {
      setProbed(true);
    }
  }

  useEffect(() => {
    refreshStatus();
  }, []);

  async function handleSeed() {
    setBusy("seed");
    setError(null);
    try {
      const res = await seedDemo();
      setStatus({ enabled: res.enabled, seeded: res.seeded, counts: res.counts });
      setCredentials(res.demo_credentials);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Seed failed");
    } finally {
      setBusy(null);
    }
  }

  async function handleReset() {
    if (!confirm("Remove all demo data and the demo user? This cannot be undone (real data is untouched).")) return;
    setBusy("reset");
    setError(null);
    try {
      const res = await resetDemo();
      setStatus({ enabled: res.enabled, seeded: res.seeded, counts: res.counts });
      setCredentials(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reset failed");
    } finally {
      setBusy(null);
    }
  }

  async function handleSignInAsDemo() {
    if (!credentials) return;
    setBusy("signin");
    setError(null);
    try {
      const res = await signin(credentials);
      setSession(res.token.access_token, res.user);
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed");
      setBusy(null);
    }
  }

  // Auto-hide the section entirely until we've heard back from the backend
  // and it's enabled. Production builds with ENABLE_DEMO_MODE=false never
  // render the section.
  if (!probed) return null;
  if (!status || !status.enabled) return null;

  return (
    <section id="demo" className="py-20 sm:py-24 bg-gradient-to-br from-pink-50 via-white to-rose-50">
      <div className="mx-auto max-w-4xl px-6">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-pink-600 text-white px-3 py-1 text-xs font-medium mb-3">
            <Sparkles className="h-3 w-3" />
            Try it live
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">See it in action</h2>
          <p className="mt-3 text-base text-gray-600 max-w-2xl mx-auto">
            One click loads a realistic incident-response dataset and creates a demo user. Sign in
            as that user, explore every feature, then tear it all down when you're done.
          </p>
        </div>

        <div className="rounded-2xl border border-pink-200 bg-white shadow-lg p-6 sm:p-8">
          {!status.seeded ? (
            <EmptyPanel onSeed={handleSeed} busy={busy} />
          ) : (
            <SeededPanel
              counts={status.counts}
              credentials={credentials}
              busy={busy}
              onSignIn={handleSignInAsDemo}
              onReset={handleReset}
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

function EmptyPanel({ onSeed, busy }: { onSeed: () => void; busy: string | null }) {
  return (
    <div className="space-y-5 text-center">
      <p className="text-sm text-gray-700">
        Demo workspace is empty. Click below to populate ~25 rows across crises, signals, stakeholders,
        resources, simulations, media mentions, and a legal hold — plus a pre-created demo user you can sign in as.
      </p>
      <Button
        size="lg"
        onClick={onSeed}
        disabled={busy !== null}
        className="bg-pink-600 hover:bg-pink-700"
      >
        {busy === "seed" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
        Seed demo data
      </Button>
      <p className="text-[11px] text-gray-500">
        Demo rows are tagged with a <code className="bg-slate-100 px-1 py-0.5 rounded">DEMO:</code> prefix.
        Clearing only removes those — anything you add yourself stays.
      </p>
    </div>
  );
}

interface SeededPanelProps {
  counts: DemoCounts;
  credentials: DemoCredentials | null;
  busy: string | null;
  onSignIn: () => void;
  onReset: () => void;
}

function SeededPanel({ counts, credentials, busy, onSignIn, onReset }: SeededPanelProps) {
  return (
    <div className="space-y-6">
      <p className="text-sm text-center text-gray-700">
        Demo data loaded. Sign in as the demo user to explore every feature page — the AI Copilot is ready
        in the bottom-right corner from the moment you land.
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {ENTITIES.filter(e => counts[e.key] > 0).map(({ key, label }) => {
          const Icon = ENTITY_ICON[key] || Zap;
          return (
            <div
              key={key}
              className="rounded-lg border border-slate-200 bg-white p-3 flex items-center gap-3"
            >
              <Icon className="h-4 w-4 text-pink-600 shrink-0" />
              <div>
                <div className="text-2xl font-bold text-gray-900 tabular-nums leading-none">{counts[key]}</div>
                <div className="text-[11px] text-slate-600 mt-1">{label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {credentials && <CredentialsCard creds={credentials} />}

      <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2 border-t border-slate-100">
        {credentials && (
          <Button
            size="lg"
            onClick={onSignIn}
            disabled={busy !== null}
            className="bg-pink-600 hover:bg-pink-700 w-full sm:w-auto"
          >
            {busy === "signin" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Sign in as demo user →
          </Button>
        )}
        <Button
          size="lg"
          variant="outline"
          onClick={onReset}
          disabled={busy !== null}
          className="text-red-700 border-red-200 hover:bg-red-50 hover:text-red-800"
        >
          {busy === "reset" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
          Clear demo data
        </Button>
      </div>

      {!credentials && (
        <p className="text-center text-[11px] text-gray-500">
          Demo already seeded in another tab. Use the credentials shown when you first ran Seed, or click
          Clear and re-seed to retrieve them.
        </p>
      )}
    </div>
  );
}

function CredentialsCard({ creds }: { creds: DemoCredentials }) {
  const [copied, setCopied] = useState<"email" | "password" | null>(null);
  async function copy(value: string, which: "email" | "password") {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(which);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      // ignore — clipboard may not be available in some embeds
    }
  }
  return (
    <div className="rounded-lg border border-pink-200 bg-pink-50 p-3 space-y-2 text-sm">
      <div className="text-xs font-semibold text-pink-700 uppercase tracking-wide">Demo credentials</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <CredRow label="Email" value={creds.email} which="email" copied={copied} onCopy={copy} />
        <CredRow label="Password" value={creds.password} which="password" copied={copied} onCopy={copy} />
      </div>
      <p className="text-[11px] text-slate-600">
        Or just click <strong>Sign in as demo user</strong> below — we'll log you in automatically.
      </p>
    </div>
  );
}

function CredRow({
  label,
  value,
  which,
  copied,
  onCopy,
}: {
  label: string;
  value: string;
  which: "email" | "password";
  copied: "email" | "password" | null;
  onCopy: (v: string, w: "email" | "password") => void;
}) {
  return (
    <button
      onClick={() => onCopy(value, which)}
      className="flex items-center justify-between gap-2 rounded border border-pink-200 bg-white px-3 py-2 text-xs hover:border-pink-400 hover:bg-pink-50 transition"
      type="button"
    >
      <span className="text-slate-500">{label}</span>
      <span className="flex items-center gap-2">
        <code className="font-mono text-slate-800">{value}</code>
        {copied === which ? (
          <span className="text-pink-700 font-medium">copied</span>
        ) : (
          <Copy className="h-3 w-3 text-slate-400" />
        )}
      </span>
    </button>
  );
}
