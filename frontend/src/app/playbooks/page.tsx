"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listPlaybooks, createPlaybook, updatePlaybook, deletePlaybook, type Playbook, type PlaybookStep, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";

export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editPb, setEditPb] = useState<Playbook | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listPlaybooks();
      setPlaybooks(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function stepsFromForm(form: FormData): PlaybookStep[] {
    const steps: PlaybookStep[] = [];
    let i = 0;
    while (form.get(`step_title_${i}`)) {
      steps.push({
        order: i + 1,
        title: String(form.get(`step_title_${i}`)),
        description: String(form.get(`step_desc_${i}`) || ""),
        suggested_assignee_role: String(form.get(`step_role_${i}`) || ""),
      });
      i++;
    }
    return steps;
  }

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get("name")),
      category: String(form.get("category")) as Playbook["category"],
      description: String(form.get("description") || ""),
      steps: stepsFromForm(form),
    };
    try {
      await createPlaybook(payload);
      setOpen(false);
      load();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to create playbook");
    }
  }

  async function handleEdit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!editPb) return;
    const form = new FormData(e.currentTarget);
    const payload: Partial<Playbook> = {
      name: String(form.get("name")),
      category: String(form.get("category")) as Playbook["category"],
      description: String(form.get("description") || ""),
      steps: stepsFromForm(form),
    };
    try {
      await updatePlaybook(editPb.id, payload);
      setEditPb(null);
      load();
    } catch (err) {
      alert("Update failed");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this playbook?")) return;
    try {
      await deletePlaybook(id);
      load();
    } catch (err) {
      alert("Delete failed");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Playbooks</h1>
          <p className="text-sm text-gray-500">Crisis response templates</p>
        </div>
        <div className="flex gap-3">
          <Link href="/dashboard"><Button variant="outline">Dashboard</Button></Link>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>Create Playbook</Button>
            <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
              <DialogHeader><DialogTitle>Create Playbook</DialogTitle></DialogHeader>
              <PlaybookForm onSubmit={handleCreate} />
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-4">
        <Card>
          <CardHeader><CardTitle>Response Playbooks</CardTitle></CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-gray-400">Loading...</p>
            ) : playbooks.length === 0 ? (
              <p className="text-sm text-gray-400">No playbooks found.</p>
            ) : (
              <div className="space-y-4">
                {playbooks.map((pb) => (
                  <div key={pb.id} className="border rounded-lg p-4 bg-white space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{pb.name}</div>
                        <div className="text-sm text-gray-600">{pb.description || "No description"}</div>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant="outline">{pb.category.replace("_", " ")}</Badge>
                        <Button size="sm" variant="outline" onClick={() => setEditPb(pb)}>Edit</Button>
                        <Button size="sm" variant="destructive" onClick={() => handleDelete(pb.id)}>Delete</Button>
                      </div>
                    </div>
                    <div className="pl-4 border-l-2 border-gray-200 space-y-2">
                      {pb.steps.map((s) => (
                        <div key={s.order} className="text-sm">
                          <span className="font-medium">{s.order}. {s.title}</span>
                          {s.suggested_assignee_role ? <span className="text-gray-500 ml-2">({s.suggested_assignee_role})</span> : null}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {editPb && (
        <Dialog open={!!editPb} onOpenChange={(v) => { if (!v) setEditPb(null); }}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Edit Playbook</DialogTitle></DialogHeader>
            <PlaybookForm onSubmit={handleEdit} initial={editPb} />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function PlaybookForm({ onSubmit, initial }: { onSubmit: (e: React.FormEvent<HTMLFormElement>) => void; initial?: Playbook }) {
  const [stepCount, setStepCount] = useState(initial?.steps.length || 1);

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div><Label>Name</Label><Input name="name" defaultValue={initial?.name} required /></div>
      <div><Label>Description</Label><Input name="description" defaultValue={initial?.description || ""} /></div>
      <div>
        <Label>Category</Label>
        <Select name="category" defaultValue={initial?.category || "other"}>
          
          
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
      <div className="space-y-2">
        <Label>Steps</Label>
        {Array.from({ length: stepCount }).map((_, i) => (
          <div key={i} className="grid grid-cols-12 gap-2">
            <div className="col-span-4"><Input name={`step_title_${i}`} placeholder="Title" defaultValue={initial?.steps[i]?.title} required /></div>
            <div className="col-span-4"><Input name={`step_desc_${i}`} placeholder="Description" defaultValue={initial?.steps[i]?.description} /></div>
            <div className="col-span-4"><Input name={`step_role_${i}`} placeholder="Role" defaultValue={initial?.steps[i]?.suggested_assignee_role} /></div>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={() => setStepCount((n) => n + 1)}>+ Add Step</Button>
      </div>
      <Button type="submit" className="w-full">Save</Button>
    </form>
  );
}
