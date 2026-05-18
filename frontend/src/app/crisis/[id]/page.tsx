"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getCrisis, updateCrisis, listActionItems, listCommunications, createActionItem, createCommunication, summarizeCrisis, getNextAction, draftCommunication, generatePostMortem, suggestPlaybookUpdates, type Crisis, type ActionItem, type Communication, type NextAction, type PostMortem, type PlaybookAdvice, ApiError } from "@/lib/api";
import { Sparkles, Loader2, BookOpen, ScrollText } from "lucide-react";
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
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [nextAction, setNextAction] = useState<NextAction | null>(null);
  const [nextActionLoading, setNextActionLoading] = useState(false);
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftedMessage, setDraftedMessage] = useState<string>("");
  const [aiError, setAiError] = useState<string | null>(null);
  const [postMortem, setPostMortem] = useState<PostMortem | null>(null);
  const [postMortemLoading, setPostMortemLoading] = useState(false);
  const [advice, setAdvice] = useState<PlaybookAdvice | null>(null);
  const [adviceLoading, setAdviceLoading] = useState(false);

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

  async function handleSummarize() {
    setSummaryLoading(true);
    setAiError(null);
    try {
      const res = await summarizeCrisis(id);
      setSummary(res.summary);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Summary failed");
    } finally {
      setSummaryLoading(false);
    }
  }

  async function handleNextAction() {
    setNextActionLoading(true);
    setAiError(null);
    try {
      const res = await getNextAction(id);
      setNextAction(res);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Next action failed");
    } finally {
      setNextActionLoading(false);
    }
  }

  async function handleCreateRecommendedAction() {
    if (!nextAction) return;
    try {
      await createActionItem({
        crisis_id: id,
        title: nextAction.title,
        description: nextAction.description,
        status: "pending",
        priority: nextAction.priority as ActionItem["priority"],
      });
      setNextAction(null);
      load();
    } catch {
      alert("Failed to create action item");
    }
  }

  async function handlePostMortem() {
    setPostMortemLoading(true);
    setAiError(null);
    try {
      const res = await generatePostMortem(id);
      setPostMortem(res);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Post-mortem failed");
    } finally {
      setPostMortemLoading(false);
    }
  }

  async function handleSuggestPlaybook() {
    setAdviceLoading(true);
    setAiError(null);
    try {
      const res = await suggestPlaybookUpdates(id);
      setAdvice(res);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Playbook suggestion failed");
    } finally {
      setAdviceLoading(false);
    }
  }

  async function handleDraftComm(commType: string, channel: string, audience?: string) {
    setDraftLoading(true);
    setAiError(null);
    try {
      const res = await draftCommunication({ crisis_id: id, comm_type: commType, channel, audience });
      setDraftedMessage(res.draft);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setDraftLoading(false);
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

          <Card>
            <CardHeader className="flex flex-row items-center gap-2">
              <Sparkles className="h-4 w-4 text-pink-600" />
              <CardTitle className="text-base">AI Copilot Tools</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-col gap-2">
                <Button onClick={handleSummarize} size="sm" variant="outline" disabled={summaryLoading}>
                  {summaryLoading ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : null}
                  Generate executive summary
                </Button>
                <Button onClick={handleNextAction} size="sm" variant="outline" disabled={nextActionLoading}>
                  {nextActionLoading ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : null}
                  Recommend next action
                </Button>
                <Button onClick={handlePostMortem} size="sm" variant="outline" disabled={postMortemLoading}>
                  {postMortemLoading ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : <ScrollText className="h-3 w-3 mr-2" />}
                  AI Post-Mortem
                </Button>
                <Button onClick={handleSuggestPlaybook} size="sm" variant="outline" disabled={adviceLoading}>
                  {adviceLoading ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : <BookOpen className="h-3 w-3 mr-2" />}
                  Suggest playbook updates
                </Button>
              </div>
              {(crisis.status !== "resolved" && crisis.status !== "contained" && crisis.status !== "post_mortem") && (
                <p className="text-[11px] text-gray-500 italic">
                  Post-mortem and playbook suggestions work best on resolved or contained crises.
                </p>
              )}
              {aiError && (
                <div className="text-xs bg-red-50 border border-red-200 text-red-700 rounded p-2">{aiError}</div>
              )}
              {summary && (
                <div className="border border-pink-200 bg-pink-50 rounded p-3">
                  <div className="text-xs font-semibold text-pink-700 mb-1 uppercase tracking-wide">AI Summary</div>
                  <div className="text-sm text-slate-800 whitespace-pre-wrap">{summary}</div>
                </div>
              )}
              {nextAction && (
                <div className="border border-pink-200 bg-pink-50 rounded p-3 space-y-2">
                  <div className="text-xs font-semibold text-pink-700 uppercase tracking-wide">Recommended Next Action</div>
                  <div className="font-medium text-sm">{nextAction.title}</div>
                  <div className="text-sm text-slate-700">{nextAction.description}</div>
                  <div className="text-xs text-slate-500">
                    Priority: <span className="font-semibold">{nextAction.priority}</span> · Suggested role: {nextAction.suggested_assignee_role}
                  </div>
                  <div className="text-xs italic text-slate-600">Why: {nextAction.rationale}</div>
                  <Button onClick={handleCreateRecommendedAction} size="sm" className="w-full">Create this action item</Button>
                </div>
              )}
              {postMortem && (
                <div className="border border-pink-200 bg-pink-50 rounded p-3 space-y-2 text-sm">
                  <div className="text-xs font-semibold text-pink-700 uppercase tracking-wide">AI Post-Mortem {postMortem.is_speculative && <span className="text-amber-700 normal-case font-normal">· speculative</span>}</div>
                  <div>
                    <div className="text-xs uppercase font-medium text-slate-500 mt-1">Timeline</div>
                    <div className="text-slate-800">{postMortem.timeline_summary}</div>
                  </div>
                  <div>
                    <div className="text-xs uppercase font-medium text-slate-500 mt-2">Root cause</div>
                    <div className="text-slate-800">{postMortem.root_cause}</div>
                  </div>
                  {postMortem.what_went_well.length > 0 && (
                    <div>
                      <div className="text-xs uppercase font-medium text-emerald-700 mt-2">What went well</div>
                      <ul className="list-disc pl-5 text-slate-800 space-y-0.5">
                        {postMortem.what_went_well.map((x, i) => <li key={i}>{x}</li>)}
                      </ul>
                    </div>
                  )}
                  {postMortem.what_went_poorly.length > 0 && (
                    <div>
                      <div className="text-xs uppercase font-medium text-red-700 mt-2">What went poorly</div>
                      <ul className="list-disc pl-5 text-slate-800 space-y-0.5">
                        {postMortem.what_went_poorly.map((x, i) => <li key={i}>{x}</li>)}
                      </ul>
                    </div>
                  )}
                  {postMortem.lessons_learned.length > 0 && (
                    <div>
                      <div className="text-xs uppercase font-medium text-slate-500 mt-2">Lessons learned</div>
                      <ul className="list-disc pl-5 text-slate-800 space-y-0.5">
                        {postMortem.lessons_learned.map((x, i) => <li key={i}>{x}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              {advice && (
                <div className="border border-pink-200 bg-pink-50 rounded p-3 space-y-2 text-sm">
                  <div className="text-xs font-semibold text-pink-700 uppercase tracking-wide">Suggested Playbook Updates</div>
                  {advice.playbook_name ? (
                    <div className="text-xs text-slate-600">
                      Target playbook: <span className="font-medium">{advice.playbook_name}</span>
                    </div>
                  ) : null}
                  {advice.summary && <div className="text-slate-800">{advice.summary}</div>}
                  {advice.suggested_changes.length === 0 ? (
                    <div className="text-xs text-slate-500 italic">No changes suggested.</div>
                  ) : (
                    <ul className="space-y-2">
                      {advice.suggested_changes.map((c, i) => (
                        <li key={i} className="bg-white rounded border border-pink-100 p-2">
                          <div className="text-[10px] uppercase tracking-wide text-pink-700 font-semibold">
                            {c.kind.replace("_", " ")}
                            {c.step_order != null && <span className="text-slate-500"> · step {c.step_order}</span>}
                          </div>
                          {c.new_title && <div className="font-medium">{c.new_title}</div>}
                          {c.new_description && <div className="text-slate-700">{c.new_description}</div>}
                          {c.new_role && <div className="text-xs text-slate-600">Role: {c.new_role}</div>}
                          <div className="text-xs italic text-slate-600 mt-1">Why: {c.rationale}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
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
              <Dialog open={commOpen} onOpenChange={(o) => { setCommOpen(o); if (!o) { setDraftedMessage(""); } }}>
                <Button onClick={() => setCommOpen(true)} size="sm">Post Update</Button>
                <DialogContent className="max-w-md">
                  <DialogHeader><DialogTitle>Post Communication</DialogTitle></DialogHeader>
                  <form onSubmit={handleAddComm} className="space-y-4">
                    <div>
                      <Label>Message</Label>
                      <textarea
                        name="message"
                        required
                        rows={5}
                        defaultValue={draftedMessage}
                        key={draftedMessage}
                        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="mt-2 w-full"
                        onClick={() => {
                          const form = document.querySelector<HTMLFormElement>('form');
                          const typeEl = form?.elements.namedItem('comm_type') as HTMLSelectElement | null;
                          const chanEl = form?.elements.namedItem('channel') as HTMLSelectElement | null;
                          handleDraftComm(typeEl?.value || 'internal_update', chanEl?.value || 'app');
                        }}
                        disabled={draftLoading}
                      >
                        {draftLoading ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : <Sparkles className="h-3 w-3 mr-2" />}
                        AI draft this message
                      </Button>
                    </div>
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
