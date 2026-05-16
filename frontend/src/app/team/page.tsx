"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listTeamMembers, createTeamMember, updateTeamMember, deleteTeamMember, type TeamMember, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function TeamPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [editMember, setEditMember] = useState<TeamMember | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listTeamMembers();
      setMembers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = members.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.email.toLowerCase().includes(search.toLowerCase()) ||
    m.role.toLowerCase().includes(search.toLowerCase()) ||
    (m.department ?? "").toLowerCase().includes(search.toLowerCase())
  );

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get("name")),
      email: String(form.get("email")),
      role: String(form.get("role")),
      department: String(form.get("department") || ""),
      phone: String(form.get("phone") || ""),
      is_active: true,
    };
    try {
      await createTeamMember(payload);
      setOpen(false);
      load();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to create team member");
    }
  }

  async function handleEdit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!editMember) return;
    const form = new FormData(e.currentTarget);
    const payload: Partial<TeamMember> = {
      name: String(form.get("name")),
      email: String(form.get("email")),
      role: String(form.get("role")),
      department: String(form.get("department") || ""),
      phone: String(form.get("phone") || ""),
      is_active: form.get("is_active") === "on",
    };
    try {
      await updateTeamMember(editMember.id, payload);
      setEditMember(null);
      load();
    } catch (err) {
      alert("Update failed");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this team member?")) return;
    try {
      await deleteTeamMember(id);
      load();
    } catch (err) {
      alert("Delete failed");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
          <p className="text-sm text-gray-500">Crisis response roster</p>
        </div>
        <div className="flex gap-3">
          <Link href="/"><Button variant="outline">Dashboard</Button></Link>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>Add Member</Button>
            <DialogContent className="max-w-md">
              <DialogHeader><DialogTitle>Add Team Member</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div><Label>Name</Label><Input name="name" required /></div>
                <div><Label>Email</Label><Input name="email" type="email" required /></div>
                <div><Label>Role</Label><Input name="role" required /></div>
                <div><Label>Department</Label><Input name="department" /></div>
                <div><Label>Phone</Label><Input name="phone" /></div>
                <Button type="submit" className="w-full">Add</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-4">
        <Input placeholder="Search team members..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-sm" />
        <Card>
          <CardHeader><CardTitle>Response Team</CardTitle></CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-gray-400">Loading...</p>
            ) : filtered.length === 0 ? (
              <p className="text-sm text-gray-400">No team members found.</p>
            ) : (
              <div className="space-y-3">
                {filtered.map((m) => (
                  <div key={m.id} className="flex items-center justify-between border rounded-lg p-4 bg-white">
                    <div>
                      <div className="font-semibold">{m.name}</div>
                      <div className="text-sm text-gray-600">{m.email} — {m.role}</div>
                      {m.department ? <div className="text-xs text-gray-500">{m.department}</div> : null}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={m.is_active ? "default" : "secondary"}>{m.is_active ? "Active" : "Inactive"}</Badge>
                      <Button size="sm" variant="outline" onClick={() => setEditMember(m)}>Edit</Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDelete(m.id)}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {editMember && (
        <Dialog open={!!editMember} onOpenChange={(v) => { if (!v) setEditMember(null); }}>
          <DialogContent className="max-w-md">
            <DialogHeader><DialogTitle>Edit Team Member</DialogTitle></DialogHeader>
            <form onSubmit={handleEdit} className="space-y-4">
              <div><Label>Name</Label><Input name="name" defaultValue={editMember.name} required /></div>
              <div><Label>Email</Label><Input name="email" type="email" defaultValue={editMember.email} required /></div>
              <div><Label>Role</Label><Input name="role" defaultValue={editMember.role} required /></div>
              <div><Label>Department</Label><Input name="department" defaultValue={editMember.department || ""} /></div>
              <div><Label>Phone</Label><Input name="phone" defaultValue={editMember.phone || ""} /></div>
              <div className="flex items-center gap-2">
                <input type="checkbox" name="is_active" id="is_active" defaultChecked={editMember.is_active} />
                <Label htmlFor="is_active">Active</Label>
              </div>
              <Button type="submit" className="w-full">Save</Button>
            </form>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
