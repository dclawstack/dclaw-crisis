"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCrises, createCrisis, deleteCrisis, type Crisis, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";

function severityColor(sev: string) {
  switch (sev) {
    case "critical": return "bg-red-600 text-white";
    case "high": return "bg-orange-500 text-white";
    case "medium": return "bg-yellow-500 text-black";
    default: return "bg-blue-500 text-white";
  }
}

function statusColor(st: string) {
  switch (st) {
    case "resolved": return "bg-green-500 text-white";
    case "contained": return "bg-teal-500 text-white";
    case "responding": return "bg-indigo-500 text-white";
    case "assessing": return "bg-purple-500 text-white";
    default: return "bg-gray-500 text-white";
  }
}

export default function CrisisListPage() {
  const [crises, setCrises] = useState<Crisis[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterSeverity, setFilterSeverity] = useState<string>("");
  const [open, setOpen] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const params: { status?: string; severity?: string } = {};
      if (filterStatus) params.status = filterStatus;
      if (filterSeverity) params.severity = filterSeverity;
      const data = await listCrises(params);
      setCrises(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filterStatus, filterSeverity]);

  const filtered = crises.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    (c.description ?? "").toLowerCase().includes(search.toLowerCase())
  );

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      title: String(form.get("title")),
      description: String(form.get("description") || ""),
      severity: String(form.get("severity")) as Crisis["severity"],
      status: "detected" as Crisis["status"],
      category: String(form.get("category")) as Crisis["category"],
      estimated_impact_usd: form.get("estimated_impact_usd") ? parseFloat(String(form.get("estimated_impact_usd"))) : undefined,
    };
    try {
      await createCrisis(payload);
      setOpen(false);
      load();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to create crisis");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this crisis?")) return;
    try {
      await deleteCrisis(id);
      load();
    } catch (err) {
      alert("Delete failed");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Crises</h1>
          <p className="text-sm text-gray-500">Manage and track all incidents</p>
        </div>
        <div className="flex gap-3">
          <Link href="/"><Button variant="outline">Dashboard</Button></Link>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>Declare Crisis</Button>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Declare New Crisis</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div><Label>Title</Label><Input name="title" required /></div>
                <div><Label>Description</Label><Input name="description" /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Severity</Label>
                    <Select name="severity" defaultValue="medium">
                      
                      
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      
                    </Select>
                  </div>
                  <div>
                    <Label>Category</Label>
                    <Select name="category" defaultValue="other">
                      
                      
                        <option value="operational">Operational</option>
                        <option value="security">Security</option>
                        <option value="legal">Legal</option>
                        <option value="pr">PR</option>
                        <option value="supply_chain">Supply Chain</option>
                        <option value="hr">HR</option>
                        <option value="financial">Financial</option>
                        <option value="other">Other</option>
                      
                    </Select>
                  </div>
                </div>
                <div><Label>Est. Impact (USD)</Label><Input name="estimated_impact_usd" type="number" /></div>
                <Button type="submit" className="w-full">Declare</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <Input placeholder="Search crises..." value={search} onChange={(e) => setSearch(e.target.value)} className="sm:max-w-sm" />
          <Select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            
            
              <option value=" ">All statuses</option>
              <option value="detected">Detected</option>
              <option value="assessing">Assessing</option>
              <option value="responding">Responding</option>
              <option value="contained">Contained</option>
              <option value="resolved">Resolved</option>
              <option value="post_mortem">Post Mortem</option>
            
          </Select>
          <Select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
            
            
              <option value=" ">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            
          </Select>
        </div>

        <Card>
          <CardHeader><CardTitle>All Crises</CardTitle></CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-gray-400">Loading...</p>
            ) : filtered.length === 0 ? (
              <p className="text-sm text-gray-400">No crises found.</p>
            ) : (
              <div className="space-y-3">
                {filtered.map((c) => (
                  <div key={c.id} className="flex items-center justify-between border rounded-lg p-4 bg-white">
                    <div className="flex-1 min-w-0">
                      <Link href={`/crisis/${c.id}`} className="font-semibold text-blue-700 hover:underline block truncate">
                        {c.title}
                      </Link>
                      <div className="text-xs text-gray-500 mt-1">{c.category.replace("_", " ")} — {new Date(c.created_at).toLocaleString()}</div>
                    </div>
                    <div className="flex items-center gap-2 ml-4 shrink-0">
                      <Badge className={severityColor(c.severity)}>{c.severity}</Badge>
                      <Badge className={statusColor(c.status)}>{c.status.replace("_", " ")}</Badge>
                      <Button size="sm" variant="destructive" onClick={() => handleDelete(c.id)}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
