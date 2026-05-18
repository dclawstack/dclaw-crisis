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

// Crisis Detection — Signals
export type SignalStatus = "new" | "triaged" | "promoted" | "dismissed";

export interface Signal {
  id: string;
  source: string;
  source_url: string | null;
  raw_text: string;
  ai_summary: string | null;
  ai_severity: "critical" | "high" | "medium" | "low" | null;
  ai_category: Crisis["category"] | null;
  ai_confidence: number | null;
  ai_rationale: string | null;
  ai_recommends_promotion: boolean;
  status: SignalStatus;
  crisis_id: string | null;
  detected_at: string;
  created_at: string;
  updated_at: string;
}

export async function listSignals(status?: SignalStatus) {
  const query = new URLSearchParams();
  if (status) query.set("status", status);
  return fetchJson<Signal[]>(`/api/v1/signals/?${query.toString()}`);
}

export async function ingestSignal(payload: { source: string; raw_text: string; source_url?: string; auto_score?: boolean }) {
  return fetchJson<Signal>("/api/v1/signals/", { method: "POST", body: JSON.stringify(payload) });
}

export async function rescoreSignal(id: string) {
  return fetchJson<Signal>(`/api/v1/signals/${id}/rescore`, { method: "POST" });
}

export async function triageSignal(id: string) {
  return fetchJson<Signal>(`/api/v1/signals/${id}/triage`, { method: "POST" });
}

export async function dismissSignal(id: string) {
  return fetchJson<Signal>(`/api/v1/signals/${id}/dismiss`, { method: "POST" });
}

export async function promoteSignal(
  id: string,
  payload: { title?: string; description?: string; severity_override?: string } = {},
) {
  return fetchJson<Signal>(`/api/v1/signals/${id}/promote`, { method: "POST", body: JSON.stringify(payload) });
}

// Playbook templating
export async function seedPlaybooks() {
  return fetchJson<{ created: number; skipped: number }>("/api/v1/playbooks/seed", { method: "POST" });
}

export interface InstantiateResult {
  crisis: Crisis;
  ai_customized: boolean;
}

export async function instantiatePlaybook(
  id: string,
  payload: {
    title: string;
    description?: string;
    severity?: string;
    incident_context?: string;
    ai_customize?: boolean;
  },
) {
  return fetchJson<InstantiateResult>(`/api/v1/playbooks/${id}/instantiate`, {
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

export interface PostMortem {
  timeline_summary: string;
  what_went_well: string[];
  what_went_poorly: string[];
  root_cause: string;
  lessons_learned: string[];
  is_speculative: boolean;
}

export async function generatePostMortem(crisisId: string) {
  return fetchJson<PostMortem>(`/api/v1/crisis/${crisisId}/post-mortem`, { method: "POST" });
}

export interface PlaybookChange {
  kind: "add_step" | "rewrite_step" | "remove_step" | "change_role";
  step_order: number | null;
  new_title: string | null;
  new_description: string | null;
  new_role: string | null;
  rationale: string;
}

export interface PlaybookAdvice {
  playbook_id: string | null;
  playbook_name: string | null;
  summary: string;
  suggested_changes: PlaybookChange[];
}

export async function suggestPlaybookUpdates(crisisId: string) {
  return fetchJson<PlaybookAdvice>(`/api/v1/crisis/${crisisId}/suggest-playbook-updates`, {
    method: "POST",
  });
}

// Stakeholders
export type StakeholderType =
  | "internal" | "customer" | "regulator" | "media" | "investor"
  | "vendor" | "partner" | "board" | "other";
export type StakeholderImportance = "critical" | "high" | "medium" | "low";

export interface Stakeholder {
  id: string;
  name: string;
  type: StakeholderType;
  organization: string | null;
  importance: StakeholderImportance;
  email: string | null;
  phone: string | null;
  tags: string[];
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function listStakeholders(params?: { type?: StakeholderType; active_only?: boolean }) {
  const query = new URLSearchParams();
  if (params?.type) query.set("type", params.type);
  if (params?.active_only) query.set("active_only", "true");
  return fetchJson<Stakeholder[]>(`/api/v1/stakeholders/?${query.toString()}`);
}

export async function createStakeholder(payload: Omit<Stakeholder, "id" | "created_at" | "updated_at">) {
  return fetchJson<Stakeholder>("/api/v1/stakeholders/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateStakeholder(id: string, payload: Partial<Omit<Stakeholder, "id" | "created_at" | "updated_at">>) {
  return fetchJson<Stakeholder>(`/api/v1/stakeholders/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteStakeholder(id: string) {
  return fetchJson<void>(`/api/v1/stakeholders/${id}`, { method: "DELETE" });
}

// Resources
export type ResourceType =
  | "war_room" | "comm_channel" | "vendor_contact" | "equipment"
  | "budget_pool" | "on_call_roster" | "external_service" | "other";
export type ResourceStatus = "available" | "reserved" | "in_use" | "unavailable";

export interface Resource {
  id: string;
  name: string;
  resource_type: ResourceType;
  status: ResourceStatus;
  capacity: string | null;
  location: string | null;
  attributes: Record<string, unknown>;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export async function listResources(params?: { status?: ResourceStatus; resource_type?: ResourceType }) {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.resource_type) query.set("resource_type", params.resource_type);
  return fetchJson<Resource[]>(`/api/v1/resources/?${query.toString()}`);
}

export async function createResource(payload: Omit<Resource, "id" | "created_at" | "updated_at">) {
  return fetchJson<Resource>("/api/v1/resources/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateResource(id: string, payload: Partial<Omit<Resource, "id" | "created_at" | "updated_at">>) {
  return fetchJson<Resource>(`/api/v1/resources/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteResource(id: string) {
  return fetchJson<void>(`/api/v1/resources/${id}`, { method: "DELETE" });
}

// Crisis-level AI tools for stakeholders/resources
export interface StakeholderPriority {
  stakeholder_id: string;
  stakeholder_name: string;
  stakeholder_type: string;
  organization: string | null;
  urgency: "immediate" | "within_4h" | "within_24h" | "post_resolution";
  channel: "phone" | "email" | "in_person" | "press_release" | "regulator_filing" | "other";
  talking_points: string[];
  rationale: string;
}

export interface StakeholderPriorities {
  priorities: StakeholderPriority[];
  notes: string;
}

export async function getStakeholderPriorities(crisisId: string) {
  return fetchJson<StakeholderPriorities>(`/api/v1/crisis/${crisisId}/stakeholder-priorities`);
}

export interface ResourceRecommendation {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  current_status: string;
  fit_score: number;
  deploy_now: boolean;
  reason: string;
  conflict_note: string | null;
}

export interface ResourceRecommendations {
  recommendations: ResourceRecommendation[];
  gaps: string[];
}

export async function getResourceRecommendations(crisisId: string) {
  return fetchJson<ResourceRecommendations>(`/api/v1/crisis/${crisisId}/recommend-resources`);
}

export { ApiError };
