"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Boxes } from "lucide-react";

import {
  listResources,
  createResource,
  updateResource,
  deleteResource,
  type Resource,
  type ResourceType,
  type ResourceStatus,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";

const TYPES: ResourceType[] = [
  "war_room", "comm_channel", "vendor_contact", "equipment",
  "budget_pool", "on_call_roster", "external_service", "other",
];
const STATUSES: ResourceStatus[] = ["available", "reserved", "in_use", "unavailable"];

const STATUS_GROUPS: { status: ResourceStatus; label: string; color: string }[] = [
  { status: "available", label: "Available", color: "bg-emerald-500" },
  { status: "reserved", label: "Reserved", color: "bg-amber-500" },
  { status: "in_use", label: "In Use", color: "bg-indigo-500" },
  { status: "unavailable", label: "Unavailable", color: "bg-slate-500" },
];

export default function ResourcesPage() {
  const [items, setItems] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<ResourceType | "">("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Resource | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listResources({ resource_type: typeFilter || undefined });
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [typeFilter]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    let attributes: Record<string, unknown> = {};
    const attrText = String(f.get("attributes_json") || "").trim();
    if (attrText) {
      try { attributes = JSON.parse(attrText); }
      catch { alert("attributes must be valid JSON"); return; }
    }
    const payload = {
      name: String(f.get("name")),
      resource_type: String(f.get("resource_type") || "other") as ResourceType,
      status: String(f.get("status") || "available") as ResourceStatus,
      capacity: String(f.get("capacity") || "") || null,
      location: String(f.get("location") || "") || null,
      attributes,
      notes: String(f.get("notes") || "") || null,
    };
    try {
      if (editing) {
        await updateResource(editing.id, payload);
      } else {
        await createResource(payload as Omit<Resource, "id" | "created_at" | "updated_at">);
      }
      setOpen(false);
      setEditing(null);
      load();
    } catch {
      alert("Save failed");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this resource?")) return;
    try {
      await deleteResource(id);
      load();
    } catch {
      alert("Delete failed");
    }
  }

  const grouped = STATUS_GROUPS.reduce<Record<ResourceStatus, Resource[]>>(
    (acc, g) => ({ ...acc, [g.status]: [] }),
    { available: [], reserved: [], in_use: [], unavailable: [] },
  );
  for (const r of items) grouped[r.status].push(r);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mt-1">
            <Boxes className="h-5 w-5 text-pink-600" />
            <h1 className="text-2xl font-bold text-gray-900">Resources</h1>
          </div>
          <p className="text-sm text-gray-500">War rooms, comm channels, vendor contacts, budget pools — assets you mobilize during a response.</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as ResourceType | "")} className="text-sm">
            <option value="">All types</option>
            {TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
          </Select>
          <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) setEditing(null); }}>
            <Button onClick={() => { setEditing(null); setOpen(true); }}>Add resource</Button>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>{editing ? "Edit" : "Add"} resource</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-3">
                <div><Label>Name</Label><Input name="name" required defaultValue={editing?.name} /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Type</Label>
                    <Select name="resource_type" defaultValue={editing?.resource_type || "other"}>
                      {TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
                    </Select>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <Select name="status" defaultValue={editing?.status || "available"}>
                      {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label>Capacity</Label><Input name="capacity" placeholder="e.g. 12 people" defaultValue={editing?.capacity || ""} /></div>
                  <div><Label>Location</Label><Input name="location" placeholder="e.g. HQ, floor 4" defaultValue={editing?.location || ""} /></div>
                </div>
                <div>
                  <Label>Attributes (JSON)</Label>
                  <textarea
                    name="attributes_json"
                    rows={3}
                    placeholder='{"secure": true, "av": "yes"}'
                    defaultValue={editing ? JSON.stringify(editing.attributes || {}, null, 2) : ""}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-pink-500"
                  />
                </div>
                <div><Label>Notes</Label>
                  <textarea name="notes" rows={2} defaultValue={editing?.notes || ""}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500" />
                </div>
                <Button type="submit" className="w-full">Save</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto">
        {loading ? (
          <div className="text-center text-gray-500">Loading…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {STATUS_GROUPS.map((g) => (
              <div key={g.status} className="bg-white rounded-lg border border-slate-200 flex flex-col">
                <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={"w-2 h-2 rounded-full " + g.color} />
                    <span className="font-semibold">{g.label}</span>
                  </div>
                  <Badge variant="outline">{grouped[g.status].length}</Badge>
                </div>
                <div className="p-3 space-y-3">
                  {grouped[g.status].length === 0 ? (
                    <div className="text-xs text-gray-400 text-center py-6">Empty</div>
                  ) : (
                    grouped[g.status].map((r) => (
                      <Card key={r.id}>
                        <CardContent className="pt-3 space-y-1.5">
                          <div className="flex items-start justify-between gap-2">
                            <div className="text-sm font-medium">{r.name}</div>
                            <Badge variant="outline" className="text-[10px]">{r.resource_type.replace("_", " ")}</Badge>
                          </div>
                          {r.capacity && <div className="text-xs text-slate-600">Capacity: {r.capacity}</div>}
                          {r.location && <div className="text-xs text-slate-600">Location: {r.location}</div>}
                          {r.notes && <div className="text-xs text-slate-500 italic">{r.notes}</div>}
                          <div className="flex gap-2 pt-1">
                            <Button size="sm" variant="outline" onClick={() => { setEditing(r); setOpen(true); }}>Edit</Button>
                            <Button size="sm" variant="destructive" onClick={() => handleDelete(r.id)}>Delete</Button>
                          </div>
                        </CardContent>
                      </Card>
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
