"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Newspaper, Loader2, Sparkles } from "lucide-react";

import {
  listMediaMentions,
  createMediaMention,
  analyzeMediaMention,
  deleteMediaMention,
  listCrises,
  type MediaMention,
  type Crisis,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";

function sentimentColor(s: MediaMention["sentiment"]) {
  switch (s) {
    case "positive": return "bg-emerald-500 text-white";
    case "negative": return "bg-red-600 text-white";
    case "mixed": return "bg-amber-500 text-white";
    case "neutral": return "bg-slate-500 text-white";
    default: return "bg-slate-300 text-slate-700";
  }
}

export default function MediaPage() {
  const [items, setItems] = useState<MediaMention[]>([]);
  const [crises, setCrises] = useState<Crisis[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [m, c] = await Promise.all([listMediaMentions(), listCrises()]);
      setItems(m);
      setCrises(c);
    } finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setCreating(true);
    try {
      await createMediaMention({
        outlet: String(f.get("outlet")),
        url: String(f.get("url") || "") || undefined,
        headline: String(f.get("headline") || "") || undefined,
        snippet: String(f.get("snippet")),
        author: String(f.get("author") || "") || undefined,
        crisis_id: String(f.get("crisis_id") || "") || undefined,
        auto_analyze: true,
      });
      setOpen(false);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Create failed");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mt-1">
            <Newspaper className="h-5 w-5 text-pink-600" />
            <h1 className="text-2xl font-bold text-gray-900">Media Monitoring</h1>
          </div>
          <p className="text-sm text-gray-500">External coverage tracked across outlets. AI scores sentiment and surfaces themes.</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <Button onClick={() => setOpen(true)}>Add mention</Button>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Ingest a media mention</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <div><Label>Outlet</Label><Input name="outlet" required placeholder="e.g. TechCrunch" /></div>
              <div><Label>Headline (optional)</Label><Input name="headline" /></div>
              <div><Label>URL (optional)</Label><Input name="url" placeholder="https://..." /></div>
              <div><Label>Author (optional)</Label><Input name="author" /></div>
              <div>
                <Label>Snippet</Label>
                <textarea name="snippet" rows={5} required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500" />
              </div>
              <div>
                <Label>Link to crisis (optional)</Label>
                <Select name="crisis_id" defaultValue="">
                  <option value="">— none —</option>
                  {crises.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
                </Select>
              </div>
              <p className="text-[11px] text-pink-700">✨ AI scores sentiment + themes on ingest.</p>
              <Button type="submit" disabled={creating} className="w-full">
                {creating && <Loader2 className="h-3 w-3 animate-spin mr-2" />}Ingest
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </header>

      <main className="p-6 max-w-7xl mx-auto">
        {loading ? <p className="text-sm text-gray-400">Loading…</p> : items.length === 0 ? (
          <p className="text-sm text-gray-400">No mentions yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {items.map((m) => (
              <Card key={m.id}>
                <CardContent className="pt-4 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs text-slate-500">{m.outlet}{m.author ? ` · ${m.author}` : ""}</div>
                      {m.headline && <div className="font-medium text-sm">{m.headline}</div>}
                    </div>
                    {m.sentiment && (
                      <div className="flex flex-col items-end gap-0.5">
                        <Badge className={sentimentColor(m.sentiment)}>{m.sentiment}</Badge>
                        {m.sentiment_score != null && (
                          <span className="text-[10px] tabular-nums text-slate-500">{m.sentiment_score >= 0 ? "+" : ""}{m.sentiment_score.toFixed(2)}</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-slate-700 line-clamp-3">{m.snippet}</div>
                  {m.key_themes.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {m.key_themes.map((t, i) => <Badge key={i} variant="outline" className="text-[10px]">{t}</Badge>)}
                    </div>
                  )}
                  <div className="text-[10px] text-slate-400">{new Date(m.mentioned_at).toLocaleString()}</div>
                  <div className="flex gap-2">
                    {m.url && <a href={m.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">Open ↗</a>}
                    {m.crisis_id && <Link href={`/crisis/${m.crisis_id}`} className="text-xs text-blue-600 hover:underline">View crisis →</Link>}
                    <Button size="sm" variant="outline" className="ml-auto" onClick={async () => {
                      setBusy(m.id);
                      try { await analyzeMediaMention(m.id); await load(); } finally { setBusy(null); }
                    }} disabled={busy !== null}>
                      {busy === m.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                    </Button>
                    <Button size="sm" variant="destructive" onClick={async () => {
                      if (!confirm("Delete?")) return;
                      await deleteMediaMention(m.id);
                      load();
                    }}>×</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
