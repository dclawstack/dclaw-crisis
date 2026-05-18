"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, RefreshCw, Sparkles, Loader2 } from "lucide-react";

import {
  listSignals,
  ingestSignal,
  rescoreSignal,
  triageSignal,
  dismissSignal,
  promoteSignal,
  type Signal,
  type SignalStatus,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const COLUMNS: { status: SignalStatus; label: string }[] = [
  { status: "new", label: "New" },
  { status: "triaged", label: "Triaged" },
  { status: "promoted", label: "Promoted" },
  { status: "dismissed", label: "Dismissed" },
];

function severityColor(sev: string | null) {
  switch (sev) {
    case "critical":
      return "bg-red-600 text-white";
    case "high":
      return "bg-orange-500 text-white";
    case "medium":
      return "bg-yellow-500 text-black";
    case "low":
      return "bg-blue-500 text-white";
    default:
      return "bg-gray-300 text-gray-700";
  }
}

export default function SignalsPage() {
  const router = useRouter();
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [ingestOpen, setIngestOpen] = useState(false);
  const [ingestBusy, setIngestBusy] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listSignals();
      setSignals(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load signals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  async function handleIngest(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setIngestBusy(true);
    try {
      await ingestSignal({
        source: String(form.get("source") || "manual"),
        source_url: String(form.get("source_url") || "") || undefined,
        raw_text: String(form.get("raw_text") || ""),
      });
      setIngestOpen(false);
      await load();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ingest failed");
    } finally {
      setIngestBusy(false);
    }
  }

  async function withBusy(id: string, action: string, fn: () => Promise<unknown>) {
    setBusyAction(`${id}:${action}`);
    setError(null);
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${action} failed`);
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePromote(s: Signal) {
    const title = window.prompt(
      "Title for the new Crisis (leave blank to use AI summary):",
      s.ai_summary || "",
    );
    if (title === null) return;
    await withBusy(s.id, "promote", async () => {
      const promoted = await promoteSignal(s.id, { title: title || undefined });
      if (promoted.crisis_id) router.push(`/crisis/${promoted.crisis_id}`);
    });
  }

  const byStatus = COLUMNS.reduce<Record<SignalStatus, Signal[]>>(
    (acc, c) => ({ ...acc, [c.status]: [] }),
    { new: [], triaged: [], promoted: [], dismissed: [] },
  );
  for (const s of signals) byStatus[s.status].push(s);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">← Dashboard</Link>
          <div className="flex items-center gap-2 mt-1">
            <AlertTriangle className="h-5 w-5 text-pink-600" />
            <h1 className="text-2xl font-bold text-gray-900">Crisis Detection</h1>
          </div>
          <p className="text-sm text-gray-500">AI-triaged signals from monitoring sources — promote real crises, dismiss noise.</p>
        </div>
        <div className="flex gap-3 items-center">
          <span className="text-xs text-gray-500 flex items-center gap-1"><RefreshCw className="h-3 w-3" /> Auto-refresh 15s</span>
          <Button variant="outline" onClick={load}>Refresh</Button>
          <Dialog open={ingestOpen} onOpenChange={setIngestOpen}>
            <Button onClick={() => setIngestOpen(true)}>Ingest Signal</Button>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Ingest a signal</DialogTitle></DialogHeader>
              <form onSubmit={handleIngest} className="space-y-4">
                <div>
                  <Label>Source</Label>
                  <Input name="source" placeholder='e.g. "manual", "rss:hackernews", "webhook:datadog"' required defaultValue="manual" />
                </div>
                <div>
                  <Label>Source URL (optional)</Label>
                  <Input name="source_url" placeholder="https://..." />
                </div>
                <div>
                  <Label>Signal text</Label>
                  <textarea
                    name="raw_text"
                    required
                    rows={6}
                    placeholder="Paste the raw alert, headline, ticket, or social-media post..."
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500"
                  />
                </div>
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Sparkles className="h-3 w-3 text-pink-600" /> AI will auto-score severity and category on ingest.
                </p>
                <Button type="submit" className="w-full" disabled={ingestBusy}>
                  {ingestBusy ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : null}
                  Ingest
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6">
        {error && (
          <div className="mb-4 max-w-7xl mx-auto bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">{error}</div>
        )}
        {loading && signals.length === 0 ? (
          <div className="text-center text-gray-500">Loading signals…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {COLUMNS.map((col) => (
              <div key={col.status} className="bg-white rounded-lg border border-slate-200 flex flex-col">
                <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                  <div className="font-semibold capitalize">{col.label}</div>
                  <Badge variant="outline">{byStatus[col.status].length}</Badge>
                </div>
                <div className="p-3 space-y-3 max-h-[70vh] overflow-y-auto">
                  {byStatus[col.status].length === 0 ? (
                    <div className="text-xs text-gray-400 text-center py-6">Empty</div>
                  ) : (
                    byStatus[col.status].map((s) => (
                      <SignalCard
                        key={s.id}
                        signal={s}
                        busyAction={busyAction}
                        onTriage={() => withBusy(s.id, "triage", () => triageSignal(s.id))}
                        onDismiss={() => withBusy(s.id, "dismiss", () => dismissSignal(s.id))}
                        onRescore={() => withBusy(s.id, "rescore", () => rescoreSignal(s.id))}
                        onPromote={() => handlePromote(s)}
                      />
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

interface SignalCardProps {
  signal: Signal;
  busyAction: string | null;
  onTriage: () => void;
  onDismiss: () => void;
  onRescore: () => void;
  onPromote: () => void;
}

function SignalCard({ signal, busyAction, onTriage, onDismiss, onRescore, onPromote }: SignalCardProps) {
  const busy = (a: string) => busyAction === `${signal.id}:${a}`;
  return (
    <Card className={signal.ai_recommends_promotion && signal.status === "new" ? "border-pink-400 shadow-pink-100 shadow" : ""}>
      <CardContent className="pt-4 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="text-xs text-gray-500 truncate flex-1">{signal.source}</div>
          {signal.ai_severity && (
            <Badge className={severityColor(signal.ai_severity)}>{signal.ai_severity}</Badge>
          )}
        </div>
        {signal.ai_summary ? (
          <div className="text-sm font-medium text-slate-800">{signal.ai_summary}</div>
        ) : (
          <div className="text-sm text-slate-700 line-clamp-3">{signal.raw_text}</div>
        )}
        {signal.ai_recommends_promotion && signal.status === "new" && (
          <div className="flex items-center gap-1 text-xs text-pink-700 bg-pink-50 border border-pink-200 rounded px-2 py-1">
            <Sparkles className="h-3 w-3" /> AI recommends promotion
          </div>
        )}
        <div className="text-xs text-gray-500 flex gap-2 flex-wrap">
          {signal.ai_category && <Badge variant="outline">{signal.ai_category.replace("_", " ")}</Badge>}
          {signal.ai_confidence != null && <span>conf {Math.round(signal.ai_confidence * 100)}%</span>}
          <span>{new Date(signal.detected_at).toLocaleString()}</span>
        </div>
        {signal.source_url && (
          <a href={signal.source_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline truncate block">
            {signal.source_url}
          </a>
        )}
        <details className="text-xs text-gray-600">
          <summary className="cursor-pointer">Raw signal</summary>
          <pre className="mt-1 whitespace-pre-wrap text-[11px] bg-slate-50 p-2 rounded">{signal.raw_text}</pre>
          {signal.ai_rationale && (
            <div className="mt-2 italic">AI rationale: {signal.ai_rationale}</div>
          )}
        </details>
        <div className="flex gap-2 flex-wrap pt-1">
          {signal.status === "new" && (
            <>
              <Button size="sm" onClick={onPromote} disabled={busy("promote")}>
                {busy("promote") && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                Promote
              </Button>
              <Button size="sm" variant="outline" onClick={onTriage} disabled={busy("triage")}>Triage</Button>
              <Button size="sm" variant="outline" onClick={onDismiss} disabled={busy("dismiss")}>Dismiss</Button>
            </>
          )}
          {signal.status === "triaged" && (
            <>
              <Button size="sm" onClick={onPromote} disabled={busy("promote")}>Promote</Button>
              <Button size="sm" variant="outline" onClick={onDismiss} disabled={busy("dismiss")}>Dismiss</Button>
            </>
          )}
          {signal.status === "dismissed" && (
            <Button size="sm" variant="outline" onClick={onPromote} disabled={busy("promote")}>Promote</Button>
          )}
          {signal.status === "promoted" && signal.crisis_id && (
            <Link href={`/crisis/${signal.crisis_id}`} className="text-xs text-blue-700 hover:underline">View crisis →</Link>
          )}
          {(signal.status === "new" || signal.status === "triaged") && (
            <Button size="sm" variant="ghost" onClick={onRescore} disabled={busy("rescore")}>
              {busy("rescore") ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
