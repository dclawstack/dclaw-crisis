"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { GraduationCap, Loader2, Play, ClipboardCheck, Sparkles } from "lucide-react";

import {
  listSimulations,
  createSimulation,
  startSimulation,
  respondSimulation,
  evaluateSimulation,
  deleteSimulation,
  type Simulation,
  type ScenarioType,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";

const TYPES: ScenarioType[] = ["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"];

function statusColor(s: Simulation["status"]) {
  switch (s) {
    case "completed": return "bg-emerald-600 text-white";
    case "running": return "bg-indigo-600 text-white";
    case "cancelled": return "bg-slate-500 text-white";
    default: return "bg-slate-300 text-slate-800";
  }
}

export default function SimulationsPage() {
  const [items, setItems] = useState<Simulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [selected, setSelected] = useState<Simulation | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try { setItems(await listSimulations()); }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to load"); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setCreating(true);
    try {
      const sim = await createSimulation({
        name: String(f.get("name")),
        scenario_type: f.get("scenario_type") as ScenarioType,
        severity: String(f.get("severity") || "high"),
        auto_generate: true,
      });
      setCreateOpen(false);
      setSelected(sim);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Create failed");
    } finally {
      setCreating(false);
    }
  }

  async function withBusy(action: string, fn: () => Promise<unknown>) {
    setBusy(action);
    setError(null);
    try { await fn(); }
    catch (e) { setError(e instanceof Error ? e.message : `${action} failed`); }
    finally { setBusy(null); }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">← Dashboard</Link>
          <div className="flex items-center gap-2 mt-1">
            <GraduationCap className="h-5 w-5 text-pink-600" />
            <h1 className="text-2xl font-bold text-gray-900">Simulations & Training</h1>
          </div>
          <p className="text-sm text-gray-500">AI-generated tabletop scenarios. Run them with your team. Evaluate the response.</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <Button onClick={() => setCreateOpen(true)}>New simulation</Button>
          <DialogContent className="max-w-md">
            <DialogHeader><DialogTitle>New simulation</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3">
              <div><Label>Name</Label><Input name="name" required placeholder="e.g. Q3 Tabletop — Security" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Type</Label>
                  <Select name="scenario_type" defaultValue="security">
                    {TYPES.map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
                  </Select>
                </div>
                <div>
                  <Label>Severity</Label>
                  <Select name="severity" defaultValue="high">
                    <option value="critical">critical</option>
                    <option value="high">high</option>
                    <option value="medium">medium</option>
                    <option value="low">low</option>
                  </Select>
                </div>
              </div>
              <p className="text-[11px] text-pink-700">✨ Scenario, expected actions, and outcomes are AI-generated on create.</p>
              <Button type="submit" disabled={creating} className="w-full">
                {creating ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : null}
                Generate scenario
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </header>

      <main className="p-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-3">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">{error}</div>}
          {loading ? <p className="text-sm text-gray-400">Loading…</p> : items.length === 0 ? (
            <p className="text-sm text-gray-400">No simulations yet.</p>
          ) : (
            items.map((s) => (
              <Card key={s.id} onClick={() => setSelected(s)} className={`cursor-pointer hover:border-pink-300 ${selected?.id === s.id ? "border-pink-400 shadow" : ""}`}>
                <CardContent className="pt-4 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-medium text-sm">{s.name}</div>
                    <Badge className={statusColor(s.status)}>{s.status}</Badge>
                  </div>
                  <div className="text-xs text-slate-500 flex gap-2 flex-wrap">
                    <Badge variant="outline">{s.scenario_type.replace("_", " ")}</Badge>
                    <Badge variant="outline">{s.severity}</Badge>
                    {s.score != null && <span className="font-semibold text-emerald-700">score {Math.round(s.score * 100)}%</span>}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <div>
          {selected ? <SimulationDetail simulation={selected} reload={load} busy={busy} withBusy={withBusy} onDelete={async () => {
            if (!confirm("Delete this simulation?")) return;
            await deleteSimulation(selected.id);
            setSelected(null);
            load();
          }} /> : (
            <Card><CardContent className="pt-6 text-sm text-gray-500">Pick a simulation on the left, or create one.</CardContent></Card>
          )}
        </div>
      </main>
    </div>
  );
}

interface DetailProps {
  simulation: Simulation;
  reload: () => Promise<void>;
  busy: string | null;
  withBusy: (a: string, f: () => Promise<unknown>) => Promise<void>;
  onDelete: () => void;
}

function SimulationDetail({ simulation, reload, busy, withBusy, onDelete }: DetailProps) {
  const [notes, setNotes] = useState(simulation.operator_notes || "");
  useEffect(() => { setNotes(simulation.operator_notes || ""); }, [simulation.id, simulation.operator_notes]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle className="text-base">{simulation.name}</CardTitle>
        <div className="flex gap-2">
          {simulation.status === "draft" && (
            <Button size="sm" onClick={() => withBusy("start", async () => { await startSimulation(simulation.id); await reload(); })} disabled={busy !== null}>
              {busy === "start" ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Play className="h-3 w-3 mr-1" />}Start
            </Button>
          )}
          <Button size="sm" variant="destructive" onClick={onDelete}>Delete</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {simulation.generated_scenario ? (
          <div className="bg-slate-50 rounded p-3 whitespace-pre-wrap text-slate-800 max-h-64 overflow-y-auto">
            {simulation.generated_scenario}
          </div>
        ) : (
          <div className="text-xs text-amber-700">No scenario generated (LLM unreachable on create). Recreate to retry.</div>
        )}

        {simulation.expected_outcomes.length > 0 && (
          <div>
            <div className="text-xs uppercase font-medium text-slate-500">Expected outcomes</div>
            <ul className="list-disc pl-5 text-slate-700">
              {simulation.expected_outcomes.map((o, i) => <li key={i}>{o}</li>)}
            </ul>
          </div>
        )}

        {simulation.generated_actions.length > 0 && (
          <div>
            <div className="text-xs uppercase font-medium text-slate-500">Expected actions</div>
            <ol className="list-decimal pl-5 text-slate-700 space-y-0.5">
              {simulation.generated_actions.map((a, i) => (
                <li key={i}><span className="font-medium">{a.action}</span>{a.role && <span className="text-xs text-slate-500"> — {a.role}</span>}</li>
              ))}
            </ol>
          </div>
        )}

        {(simulation.status === "running" || simulation.status === "draft") && (
          <div>
            <Label>Operator response notes</Label>
            <textarea
              rows={5}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Describe what the team did, in what order, and any blockers encountered."
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500"
            />
            <div className="flex gap-2 mt-2">
              <Button size="sm" variant="outline" onClick={() => withBusy("save", async () => { await respondSimulation(simulation.id, notes); await reload(); })} disabled={!notes.trim() || busy !== null}>
                Save response
              </Button>
              <Button size="sm" onClick={() => withBusy("eval", async () => {
                if (notes.trim() && notes !== simulation.operator_notes) await respondSimulation(simulation.id, notes);
                await evaluateSimulation(simulation.id);
                await reload();
              })} disabled={!notes.trim() || busy !== null}>
                {busy === "eval" ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Sparkles className="h-3 w-3 mr-1" />}
                Save + Evaluate
              </Button>
            </div>
          </div>
        )}

        {simulation.evaluation_summary && (
          <div className="border border-pink-200 bg-pink-50 rounded p-3 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-pink-700 uppercase tracking-wide">
              <ClipboardCheck className="h-3 w-3" /> AI Evaluation · score {Math.round((simulation.score || 0) * 100)}%
            </div>
            <div className="text-sm">{simulation.evaluation_summary}</div>
            {simulation.evaluation_breakdown.length > 0 && (
              <ul className="space-y-1">
                {simulation.evaluation_breakdown.map((b, i) => (
                  <li key={i} className="text-xs bg-white rounded p-2 border border-pink-100">
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-medium">{b.expected_outcome}</div>
                      <Badge className={b.achieved === "yes" ? "bg-emerald-500 text-white" : b.achieved === "partial" ? "bg-yellow-500 text-black" : "bg-red-600 text-white"}>{b.achieved}</Badge>
                    </div>
                    {b.comment && <div className="text-slate-700 mt-1">{b.comment}</div>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
