"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Users } from "lucide-react";

import {
  listStakeholders,
  createStakeholder,
  updateStakeholder,
  deleteStakeholder,
  type Stakeholder,
  type StakeholderType,
  type StakeholderImportance,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const TYPES: StakeholderType[] = [
  "internal", "customer", "regulator", "media", "investor", "vendor", "partner", "board", "other",
];
const IMPORTANCE: StakeholderImportance[] = ["critical", "high", "medium", "low"];

function importanceColor(i: StakeholderImportance) {
  switch (i) {
    case "critical": return "bg-red-600 text-white";
    case "high": return "bg-orange-500 text-white";
    case "medium": return "bg-yellow-500 text-black";
    default: return "bg-blue-500 text-white";
  }
}

export default function StakeholdersPage() {
  const [items, setItems] = useState<Stakeholder[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<StakeholderType | "">("");
  const [activeOnly, setActiveOnly] = useState(false);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Stakeholder | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listStakeholders({
        type: typeFilter || undefined,
        active_only: activeOnly || undefined,
      });
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [typeFilter, activeOnly]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const payload = {
      name: String(f.get("name")),
      type: String(f.get("type") || "other") as StakeholderType,
      organization: String(f.get("organization") || "") || null,
      importance: String(f.get("importance") || "medium") as StakeholderImportance,
      email: String(f.get("email") || "") || null,
      phone: String(f.get("phone") || "") || null,
      tags: String(f.get("tags") || "").split(",").map((t) => t.trim()).filter(Boolean),
      notes: String(f.get("notes") || "") || null,
      is_active: f.get("is_active") === "on",
    };
    try {
      if (editing) {
        await updateStakeholder(editing.id, payload);
      } else {
        await createStakeholder(payload as Omit<Stakeholder, "id" | "created_at" | "updated_at">);
      }
      setOpen(false);
      setEditing(null);
      load();
    } catch {
      alert("Save failed");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this stakeholder?")) return;
    try {
      await deleteStakeholder(id);
      load();
    } catch {
      alert("Delete failed");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mt-1">
            <Users className="h-5 w-5 text-pink-600" />
            <h1 className="text-2xl font-bold text-gray-900">Stakeholders</h1>
          </div>
          <p className="text-sm text-gray-500">Customers, regulators, media, investors, vendors — anyone you communicate with during a crisis.</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as StakeholderType | "")} className="text-sm">
            <option value="">All types</option>
            {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </Select>
          <label className="flex items-center gap-1 text-xs text-slate-600">
            <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
            Active only
          </label>
          <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) setEditing(null); }}>
            <Button onClick={() => { setEditing(null); setOpen(true); }}>Add stakeholder</Button>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>{editing ? "Edit" : "Add"} stakeholder</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-3">
                <div><Label>Name</Label><Input name="name" required defaultValue={editing?.name} /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Type</Label>
                    <Select name="type" defaultValue={editing?.type || "other"}>
                      {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                    </Select>
                  </div>
                  <div>
                    <Label>Importance</Label>
                    <Select name="importance" defaultValue={editing?.importance || "medium"}>
                      {IMPORTANCE.map((i) => <option key={i} value={i}>{i}</option>)}
                    </Select>
                  </div>
                </div>
                <div><Label>Organization</Label><Input name="organization" defaultValue={editing?.organization || ""} /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label>Email</Label><Input name="email" defaultValue={editing?.email || ""} /></div>
                  <div><Label>Phone</Label><Input name="phone" defaultValue={editing?.phone || ""} /></div>
                </div>
                <div><Label>Tags (comma separated)</Label><Input name="tags" defaultValue={editing?.tags?.join(", ") || ""} /></div>
                <div><Label>Notes</Label>
                  <textarea name="notes" rows={2} defaultValue={editing?.notes || ""}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500" />
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" name="is_active" defaultChecked={editing?.is_active !== false} />
                  Active
                </label>
                <Button type="submit" className="w-full">Save</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto">
        <Card>
          <CardHeader><CardTitle>{items.length} stakeholder{items.length === 1 ? "" : "s"}</CardTitle></CardHeader>
          <CardContent>
            {loading ? <p className="text-sm text-gray-400">Loading…</p> : items.length === 0 ? (
              <p className="text-sm text-gray-400">No stakeholders yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Organization</TableHead>
                    <TableHead>Importance</TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="font-medium">{s.name}</TableCell>
                      <TableCell><Badge variant="outline">{s.type}</Badge></TableCell>
                      <TableCell className="text-sm text-slate-600">{s.organization || "—"}</TableCell>
                      <TableCell><Badge className={importanceColor(s.importance)}>{s.importance}</Badge></TableCell>
                      <TableCell className="text-xs text-slate-600">
                        {s.email && <div>{s.email}</div>}
                        {s.phone && <div>{s.phone}</div>}
                      </TableCell>
                      <TableCell className="text-xs">{s.tags.join(", ") || "—"}</TableCell>
                      <TableCell>{s.is_active ? <Badge className="bg-emerald-500 text-white">Active</Badge> : <Badge variant="outline">Inactive</Badge>}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => { setEditing(s); setOpen(true); }}>Edit</Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDelete(s.id)}>Delete</Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
