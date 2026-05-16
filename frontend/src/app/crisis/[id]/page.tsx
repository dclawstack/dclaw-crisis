"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getCrisis, updateCrisis, listActionItems, listCommunications, createActionItem, createCommunication, type Crisis, type ActionItem, type Communication, ApiError } from "@/lib/api";
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

export default function CrisisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [crisis, setCrisis] = useState<Crisis | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [comms, setComms] = useState<Communication[]>([]);
  const [loading, setLoading] = useState(true);
  const [editOpen, setEditOpen] = useState(false);
  const [actionOpen, setActionOpen] = useState(false);
  const [commOpen, setCommOpen] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [c, a, co] = await Promise.all([
        getCrisis(id),
        listActionItems({ crisis_id: id }),
        listCommunications({ crisis_id: id }),
      ]);
      setCrisis(c);
      setActions(a);
      setComms(co);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function handleEdit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload: Partial<Crisis> = {
      title: String(form.get("title")),
      description: String(form.get("description") || ""),
      severity: String(form.get("severity")) as Crisis["severity"],
      status: String(form.get("status")) as Crisis["status"],
      category: String(form.get("category")) as Crisis["category"],
      estimated_impact_usd: form.get("estimated_impact_usd") ? parseFloat(String(form.get("estimated_impact_usd"))) : undefined,
    };
    try {
      await updateCrisis(id, payload);
      setEditOpen(false);
      load();
    } catch (err) {
      alert("Update failed");
    }
  }

  async function handleAddAction(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      crisis_id: id,
      title: String(form.get("title")),
      description: String(form.get("description") || ""),
      status: "pending" as ActionItem["status"],
      priority: String(form.get("priority")) as ActionItem["priority"],
    };
    try {
      await createActionItem(payload);
      setActionOpen(false);
      load();
    } catch (err) {
      alert("Failed to add action item");
    }
  }

  async function handleAddComm(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      crisis_id: id,
      message: String(form.get("message")),
      comm_type: String(form.get("comm_type")) as Communication["comm_type"],
      channel: String(form.get("channel")) as Communication["channel"],
    };
    try {
      await createCommunication(payload);
      setCommOpen(false);
      load();
    } catch (err) {
      alert("Failed to post communication");
    }
  }

  if (loading) return <div className="p-8">Loading...</div>;
  if (!crisis) return <div className="p-8">Crisis not found.</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <Link href="/crisis" className="text-sm text-blue-600 hover:underline">← Back to Crises</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{crisis.title}</h1>
        </div>
        <div className="flex gap-2">
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <Button onClick={() => setEditOpen(true)} variant="outline">Edit Crisis</Button>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Edit Crisis</DialogTitle></DialogHeader>
              <form onSubmit={handleEdit} className="space-y-4">
                <div><Label>Title</Label><Input name="title" defaultValue={crisis.title} required /></div>
                <div><Label>Description</Label><Input name="description" defaultValue={crisis.description || ""} /></div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <Label>Severity</Label>
                    <Select name="severity" defaultValue={crisis.severity}>
                      
                      
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      
                    </Select>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <Select name="status" defaultValue={crisis.status}>
                      
                      
                        <option value="detected">Detected</option>
                        <option value="assessing">Assessing</option>
                        <option value="responding">Responding</option>
                        <option value="contained">Contained</option>
                        <option value="resolved">Resolved</option>
                        <option value="post_mortem">Post Mortem</option>
                      
                    </Select>
                  </div>
                  <div>
                    <Label>Category</Label>
                    <Select name="category" defaultValue={crisis.category}>
                      
                      
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
                <div><Label>Est. Impact (USD)</Label><Input name="estimated_impact_usd" type="number" defaultValue={crisis.estimated_impact_usd} /></div>
                <Button type="submit" className="w-full">Save Changes</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Info Card */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader><CardTitle>Crisis Details</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2 flex-wrap">
                <Badge className={severityColor(crisis.severity)}>{crisis.severity}</Badge>
                <Badge className={statusColor(crisis.status)}>{crisis.status.replace("_", " ")}</Badge>
                <Badge variant="outline">{crisis.category.replace("_", " ")}</Badge>
              </div>
              <div className="text-sm text-gray-700">{crisis.description || "No description provided."}</div>
              {crisis.estimated_impact_usd ? (
                <div className="text-sm"><span className="font-medium">Est. Impact:</span> ${crisis.estimated_impact_usd.toLocaleString()}</div>
              ) : null}
              <div className="text-xs text-gray-500">Detected: {new Date(crisis.detected_at || crisis.created_at).toLocaleString()}</div>
            </CardContent>
          </Card>
        </div>

        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Action Items */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Action Items</CardTitle>
              <Dialog open={actionOpen} onOpenChange={setActionOpen}>
                <Button onClick={() => setActionOpen(true)} size="sm">Add Action</Button>
                <DialogContent className="max-w-md">
                  <DialogHeader><DialogTitle>New Action Item</DialogTitle></DialogHeader>
                  <form onSubmit={handleAddAction} className="space-y-4">
                    <div><Label>Title</Label><Input name="title" required /></div>
                    <div><Label>Description</Label><Input name="description" /></div>
                    <div>
                      <Label>Priority</Label>
                      <Select name="priority" defaultValue="medium">
                        
                        
                          <option value="critical">Critical</option>
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        
                      </Select>
                    </div>
                    <Button type="submit" className="w-full">Add</Button>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {actions.length === 0 ? (
                <p className="text-sm text-gray-400">No action items yet.</p>
              ) : (
                <div className="space-y-3">
                  {actions.map((a) => (
                    <div key={a.id} className="flex items-center justify-between border rounded p-3 bg-white">
                      <div>
                        <div className="font-medium">{a.title}</div>
                        <div className="text-xs text-gray-500">{a.status} — {a.priority}</div>
                      </div>
                      <Badge className={a.status === "completed" ? "bg-green-500 text-white" : a.status === "blocked" ? "bg-red-500 text-white" : "bg-yellow-500 text-black"}>
                        {a.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Communications */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Communications</CardTitle>
              <Dialog open={commOpen} onOpenChange={setCommOpen}>
                <Button onClick={() => setCommOpen(true)} size="sm">Post Update</Button>
                <DialogContent className="max-w-md">
                  <DialogHeader><DialogTitle>Post Communication</DialogTitle></DialogHeader>
                  <form onSubmit={handleAddComm} className="space-y-4">
                    <div><Label>Message</Label><Input name="message" required /></div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label>Type</Label>
                        <Select name="comm_type" defaultValue="internal_update">
                          
                          
                            <option value="internal_update">Internal Update</option>
                            <option value="stakeholder_alert">Stakeholder Alert</option>
                            <option value="public_statement">Public Statement</option>
                            <option value="exec_brief">Exec Brief</option>
                          
                        </Select>
                      </div>
                      <div>
                        <Label>Channel</Label>
                        <Select name="channel" defaultValue="app">
                          
                          
                            <option value="app">App</option>
                            <option value="email">Email</option>
                            <option value="slack">Slack</option>
                            <option value="sms">SMS</option>
                          
                        </Select>
                      </div>
                    </div>
                    <Button type="submit" className="w-full">Post</Button>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {comms.length === 0 ? (
                <p className="text-sm text-gray-400">No communications yet.</p>
              ) : (
                <div className="space-y-3">
                  {comms.map((c) => (
                    <div key={c.id} className="border rounded p-3 bg-white">
                      <div className="text-sm text-gray-800">{c.message}</div>
                      <div className="text-xs text-gray-500 mt-2 flex gap-2">
                        <Badge variant="outline">{c.comm_type.replace("_", " ")}</Badge>
                        <Badge variant="outline">{c.channel}</Badge>
                        <span>{new Date(c.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
