"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Scale, Loader2 } from "lucide-react";

import {
  listLegalHolds,
  createLegalHold,
  updateLegalHold,
  issueLegalHold,
  releaseLegalHold,
  deleteLegalHold,
  listCrises,
  type LegalHold,
  type Crisis,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";

function statusColor(s: LegalHold["status"]) {
  switch (s) {
    case "active": return "bg-red-600 text-white";
    case "released": return "bg-slate-500 text-white";
    default: return "bg-amber-500 text-white";
  }
}

export default function LegalHoldsPage() {
  const [items, setItems] = useState<LegalHold[]>([]);
  const [crises, setCrises] = useState<Crisis[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<LegalHold | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [h, c] = await Promise.all([listLegalHolds(), listCrises()]);
      setItems(h);
      setCrises(c);
    } finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const custodianText = String(f.get("custodians_text") || "");
    const custodians = custodianText.split("\n").map((line) => {
      const trimmed = line.trim();
      if (!trimmed) return null;
      const [name, email] = trimmed.split("|").map(s => s.trim());
      return { name, email };
    }).filter(Boolean) as { name: string; email?: string }[];
    const dataSources = String(f.get("data_sources_text") || "").split(",").map(s => s.trim()).filter(Boolean);
    const payload = {
      crisis_id: String(f.get("crisis_id") || "") || undefined,
      title: String(f.get("title")),
      scope_description: String(f.get("scope_description") || "") || undefined,
      custodians,
      data_sources: dataSources,
      hold_notice_text: String(f.get("hold_notice_text") || "") || undefined,
      issued_by: String(f.get("issued_by") || "") || undefined,
    };
    try {
      if (editing) await updateLegalHold(editing.id, payload);
      else await createLegalHold(payload);
      setOpen(false); setEditing(null);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Save failed");
    }
  }

  async function withBusy(id: string, fn: () => Promise<unknown>) {
    setBusy(id);
    try { await fn(); await load(); }
    catch (e) { alert(e instanceof Error ? e.message : "Action failed"); }
    finally { setBusy(null); }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mt-1">
            <Scale className="h-5 w-5 text-pink-600" />
            <h1 className="text-2xl font-bold text-gray-900">Legal Holds</h1>
          </div>
          <p className="text-sm text-gray-500">Evidence preservation orders for active matters. AI can draft notice text and recommend evidence per crisis.</p>
        </div>
        <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) setEditing(null); }}>
          <Button onClick={() => { setEditing(null); setOpen(true); }}>New hold</Button>
          <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
            <DialogHeader><DialogTitle>{editing ? "Edit hold" : "New legal hold"}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div><Label>Title</Label><Input name="title" required defaultValue={editing?.title} /></div>
              <div>
                <Label>Link to crisis (optional)</Label>
                <Select name="crisis_id" defaultValue={editing?.crisis_id || ""}>
                  <option value="">— none —</option>
                  {crises.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
                </Select>
              </div>
              <div>
                <Label>Scope description</Label>
                <textarea name="scope_description" rows={2} defaultValue={editing?.scope_description || ""} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <Label>Custodians (one per line: Name | email)</Label>
                <textarea name="custodians_text" rows={3} defaultValue={(editing?.custodians || []).map(c => `${c.name || ""}${c.email ? ` | ${c.email}` : ""}`).join("\n")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <Label>Data sources (comma separated)</Label>
                <Input name="data_sources_text" defaultValue={(editing?.data_sources || []).join(", ")} />
              </div>
              <div>
                <Label>Hold notice text (required to issue)</Label>
                <textarea name="hold_notice_text" rows={4} defaultValue={editing?.hold_notice_text || ""} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-mono text-xs" />
              </div>
              <div><Label>Issued by</Label><Input name="issued_by" defaultValue={editing?.issued_by || ""} /></div>
              <Button type="submit" className="w-full">Save</Button>
            </form>
          </DialogContent>
        </Dialog>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-3">
        {loading ? <p className="text-sm text-gray-400">Loading…</p> : items.length === 0 ? (
          <p className="text-sm text-gray-400">No legal holds yet.</p>
        ) : (
          items.map((h) => (
            <Card key={h.id}>
              <CardHeader className="flex flex-row items-center justify-between gap-2">
                <CardTitle className="text-base">{h.title}</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge className={statusColor(h.status)}>{h.status}</Badge>
                  {h.crisis_id && <Link href={`/crisis/${h.crisis_id}`} className="text-xs text-blue-600 hover:underline">View crisis →</Link>}
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {h.scope_description && <div className="text-slate-700">{h.scope_description}</div>}
                {h.custodians.length > 0 && (
                  <div className="text-xs text-slate-600">Custodians: {h.custodians.map(c => c.name || c.email).filter(Boolean).join(", ")}</div>
                )}
                {h.data_sources.length > 0 && (
                  <div className="text-xs text-slate-600">Sources: {h.data_sources.join(", ")}</div>
                )}
                {h.hold_notice_text && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-slate-600">Notice text</summary>
                    <pre className="mt-1 whitespace-pre-wrap bg-slate-50 p-2 rounded text-[11px]">{h.hold_notice_text}</pre>
                  </details>
                )}
                <div className="flex gap-2 flex-wrap pt-1">
                  {h.status === "draft" && <>
                    <Button size="sm" variant="outline" onClick={() => { setEditing(h); setOpen(true); }}>Edit</Button>
                    <Button size="sm" onClick={() => withBusy(h.id, () => issueLegalHold(h.id))} disabled={busy !== null || !h.hold_notice_text}>Issue</Button>
                    <Button size="sm" variant="destructive" onClick={() => withBusy(h.id, () => deleteLegalHold(h.id))}>Delete</Button>
                  </>}
                  {h.status === "active" && (
                    <Button size="sm" onClick={() => {
                      const reason = prompt("Reason for release?") || undefined;
                      withBusy(h.id, () => releaseLegalHold(h.id, reason));
                    }} disabled={busy !== null}>Release</Button>
                  )}
                  {h.status === "released" && (
                    <Button size="sm" variant="destructive" onClick={() => withBusy(h.id, () => deleteLegalHold(h.id))}>Delete</Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </main>
    </div>
  );
}
