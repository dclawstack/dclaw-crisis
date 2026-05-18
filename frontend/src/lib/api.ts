const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });
  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(`API error ${response.status}: ${error}`, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export async function getHealth() {
  return fetchJson<{ status: string }>("/health/");
}

// Dashboard
export async function getDashboard() {
  return fetchJson<{
    active_crises: number;
    open_action_items: number;
    critical_crises: number;
    avg_resolution_hours: number;
    severity_breakdown: Record<string, number>;
    status_breakdown: Record<string, number>;
    total_crises: number;
  }>("/api/v1/dashboard/");
}

// Crisis
export interface Crisis {
  id: string;
  title: string;
  description?: string;
  severity: "critical" | "high" | "medium" | "low";
  status: "detected" | "assessing" | "responding" | "contained" | "resolved" | "post_mortem";
  category: "operational" | "security" | "legal" | "pr" | "supply_chain" | "hr" | "financial" | "other";
  lead_id?: string;
  detected_at?: string;
  resolved_at?: string;
  estimated_impact_usd?: number;
  created_at: string;
  updated_at: string;
}

export async function listCrises(params?: { status?: string; severity?: string; category?: string }) {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.severity) query.set("severity", params.severity);
  if (params?.category) query.set("category", params.category);
  return fetchJson<Crisis[]>(`/api/v1/crisis/?${query.toString()}`);
}

export async function createCrisis(payload: Omit<Crisis, "id" | "created_at" | "updated_at">) {
  return fetchJson<Crisis>("/api/v1/crisis/", { method: "POST", body: JSON.stringify(payload) });
}

export async function getCrisis(id: string) {
  return fetchJson<Crisis>(`/api/v1/crisis/${id}`);
}

export async function updateCrisis(id: string, payload: Partial<Omit<Crisis, "id" | "created_at" | "updated_at">>) {
  return fetchJson<Crisis>(`/api/v1/crisis/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteCrisis(id: string) {
  return fetchJson<void>(`/api/v1/crisis/${id}`, { method: "DELETE" });
}

// Team Members
export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  department?: string;
  phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function listTeamMembers() {
  return fetchJson<TeamMember[]>("/api/v1/team-members/");
}

export async function createTeamMember(payload: Omit<TeamMember, "id" | "created_at" | "updated_at">) {
  return fetchJson<TeamMember>("/api/v1/team-members/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateTeamMember(id: string, payload: Partial<Omit<TeamMember, "id" | "created_at" | "updated_at">>) {
  return fetchJson<TeamMember>(`/api/v1/team-members/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteTeamMember(id: string) {
  return fetchJson<void>(`/api/v1/team-members/${id}`, { method: "DELETE" });
}

// Action Items
export interface ActionItem {
  id: string;
  crisis_id: string;
  title: string;
  description?: string;
  assignee_id?: string;
  status: "pending" | "in_progress" | "blocked" | "completed";
  priority: "critical" | "high" | "medium" | "low";
  due_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export async function listActionItems(params?: { crisis_id?: string; assignee_id?: string; status?: string }) {
  const query = new URLSearchParams();
  if (params?.crisis_id) query.set("crisis_id", params.crisis_id);
  if (params?.assignee_id) query.set("assignee_id", params.assignee_id);
  if (params?.status) query.set("status", params.status);
  return fetchJson<ActionItem[]>(`/api/v1/action-items/?${query.toString()}`);
}

export async function createActionItem(payload: Omit<ActionItem, "id" | "created_at" | "updated_at" | "completed_at">) {
  return fetchJson<ActionItem>("/api/v1/action-items/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateActionItem(id: string, payload: Partial<Omit<ActionItem, "id" | "created_at" | "updated_at">>) {
  return fetchJson<ActionItem>(`/api/v1/action-items/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteActionItem(id: string) {
  return fetchJson<void>(`/api/v1/action-items/${id}`, { method: "DELETE" });
}

// Communications
export interface Communication {
  id: string;
  crisis_id: string;
  author_id?: string;
  message: string;
  comm_type: "internal_update" | "stakeholder_alert" | "public_statement" | "exec_brief";
  channel: "app" | "email" | "slack" | "sms";
  created_at: string;
  updated_at: string;
}

export async function listCommunications(params?: { crisis_id?: string }) {
  const query = new URLSearchParams();
  if (params?.crisis_id) query.set("crisis_id", params.crisis_id);
  return fetchJson<Communication[]>(`/api/v1/communications/?${query.toString()}`);
}

export async function createCommunication(payload: Omit<Communication, "id" | "created_at" | "updated_at">) {
  return fetchJson<Communication>("/api/v1/communications/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateCommunication(id: string, payload: Partial<Omit<Communication, "id" | "created_at" | "updated_at">>) {
  return fetchJson<Communication>(`/api/v1/communications/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteCommunication(id: string) {
  return fetchJson<void>(`/api/v1/communications/${id}`, { method: "DELETE" });
}

// Playbooks
export interface PlaybookStep {
  order: number;
  title: string;
  description?: string;
  suggested_assignee_role?: string;
}

export interface Playbook {
  id: string;
  name: string;
  category: "operational" | "security" | "legal" | "pr" | "supply_chain" | "hr" | "financial" | "other";
  description?: string;
  steps: PlaybookStep[];
  created_at: string;
  updated_at: string;
}

export async function listPlaybooks() {
  return fetchJson<Playbook[]>("/api/v1/playbooks/");
}

export async function createPlaybook(payload: Omit<Playbook, "id" | "created_at" | "updated_at">) {
  return fetchJson<Playbook>("/api/v1/playbooks/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updatePlaybook(id: string, payload: Partial<Omit<Playbook, "id" | "created_at" | "updated_at">>) {
  return fetchJson<Playbook>(`/api/v1/playbooks/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deletePlaybook(id: string) {
  return fetchJson<void>(`/api/v1/playbooks/${id}`, { method: "DELETE" });
}

// Playbook templating
export async function seedPlaybooks() {
  return fetchJson<{ created: number; skipped: number }>("/api/v1/playbooks/seed", { method: "POST" });
}

export async function instantiatePlaybook(id: string, payload: { title: string; description?: string; severity?: string }) {
  return fetchJson<Crisis>(`/api/v1/playbooks/${id}/instantiate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// AI Copilot
export interface CopilotChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function copilotChat(messages: CopilotChatMessage[], focusedCrisisId?: string) {
  return fetchJson<{ reply: string }>("/api/v1/copilot/chat", {
    method: "POST",
    body: JSON.stringify({ messages, focused_crisis_id: focusedCrisisId ?? null }),
  });
}

export async function summarizeCrisis(id: string) {
  return fetchJson<{ summary: string }>(`/api/v1/crisis/${id}/summarize`, { method: "POST" });
}

export interface NextAction {
  title: string;
  description: string;
  priority: string;
  rationale: string;
  suggested_assignee_role: string;
}

export async function getNextAction(id: string) {
  return fetchJson<NextAction>(`/api/v1/crisis/${id}/next-action`);
}

export async function draftCommunication(payload: {
  crisis_id: string;
  comm_type?: string;
  channel?: string;
  audience?: string;
  extra_context?: string;
}) {
  return fetchJson<{ draft: string; comm_type: string; channel: string }>(
    "/api/v1/communications/draft",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export { ApiError };
