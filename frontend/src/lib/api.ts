const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const TOKEN_KEY = "dclaw-crisis-token";

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

function clearSessionFromApi() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem("dclaw-crisis-user");
  window.dispatchEvent(new CustomEvent("dclaw-auth-changed"));
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = readToken();
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    // Token rejected — drop the stored session so AuthGuard kicks in next paint.
    clearSessionFromApi();
  }
  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(`API error ${response.status}: ${error}`, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

// ─── Auth API ─────────────────────────────────────────────────────────────
export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  auth_provider: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface AuthSession {
  user: AuthUser;
  token: { access_token: string; token_type: "bearer"; expires_in: number };
}

export async function signup(payload: { email: string; password: string; name?: string }) {
  return fetchJson<AuthSession>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function signin(payload: { email: string; password: string }) {
  return fetchJson<AuthSession>("/api/v1/auth/signin", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMe() {
  return fetchJson<AuthUser>("/api/v1/auth/me");
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
export type DeliveryStatus = "pending" | "queued" | "sent" | "failed";
export type Sentiment = "positive" | "neutral" | "negative" | "mixed";

export interface Communication {
  id: string;
  crisis_id: string;
  author_id?: string;
  message: string;
  comm_type: "internal_update" | "stakeholder_alert" | "public_statement" | "exec_brief";
  channel: "app" | "email" | "slack" | "sms";
  delivery_status: DeliveryStatus;
  sent_at: string | null;
  delivery_log: Record<string, unknown>;
  sentiment: Sentiment | null;
  sentiment_score: number | null;
  sentiment_analyzed_at: string | null;
  predicted_reaction: string | null;
  risk_flags: string[];
  created_at: string;
  updated_at: string;
}

export async function listCommunications(params?: { crisis_id?: string }) {
  const query = new URLSearchParams();
  if (params?.crisis_id) query.set("crisis_id", params.crisis_id);
  return fetchJson<Communication[]>(`/api/v1/communications/?${query.toString()}`);
}

export interface CommunicationCreatePayload {
  crisis_id: string;
  author_id?: string;
  message: string;
  comm_type?: Communication["comm_type"];
  channel?: Communication["channel"];
}

export async function createCommunication(payload: CommunicationCreatePayload) {
  return fetchJson<Communication>("/api/v1/communications/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateCommunication(id: string, payload: Partial<CommunicationCreatePayload>) {
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

// Communication send + sentiment
export async function sendCommunication(id: string) {
  return fetchJson<Communication>(`/api/v1/communications/${id}/send`, { method: "POST" });
}

export interface SentimentResult {
  sentiment: Sentiment;
  sentiment_score: number;
  predicted_reaction: string;
  risk_flags: string[];
  analyzed_at: string;
}

export async function analyzeCommunicationSentiment(id: string) {
  return fetchJson<SentimentResult>(`/api/v1/communications/${id}/analyze-sentiment`, { method: "POST" });
}

export interface SentimentTrendPoint {
  communication_id: string;
  sentiment: Sentiment;
  sentiment_score: number;
  analyzed_at: string;
  comm_type: string;
  channel: string;
  risk_flag_count: number;
}

export interface SentimentTrend {
  crisis_id: string;
  analyzed_count: number;
  total_communications: number;
  counts: { positive: number; neutral: number; negative: number; mixed: number };
  average_score: number | null;
  trend_direction: "improving" | "worsening" | "flat" | "insufficient_data";
  points: SentimentTrendPoint[];
}

export async function getSentimentTrend(crisisId: string) {
  return fetchJson<SentimentTrend>(`/api/v1/crisis/${crisisId}/sentiment-trend`);
}

// ─── P2.1 Simulations ──────────────────────────────────────────────────────
export type ScenarioType = "operational" | "security" | "legal" | "pr" | "supply_chain" | "hr" | "financial" | "other";
export type SimulationStatus = "draft" | "running" | "completed" | "cancelled";

export interface SimulationAction {
  order: number;
  action: string;
  role: string;
}

export interface SimulationBreakdownItem {
  expected_outcome: string;
  achieved: "yes" | "partial" | "no";
  comment: string;
}

export interface Simulation {
  id: string;
  name: string;
  scenario_type: ScenarioType;
  severity: "critical" | "high" | "medium" | "low";
  participants: string[];
  status: SimulationStatus;
  generated_scenario: string | null;
  generated_actions: SimulationAction[];
  expected_outcomes: string[];
  operator_notes: string | null;
  evaluation_summary: string | null;
  score: number | null;
  evaluation_breakdown: SimulationBreakdownItem[];
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export async function listSimulations() {
  return fetchJson<Simulation[]>("/api/v1/simulations/");
}

export async function createSimulation(payload: { name: string; scenario_type?: ScenarioType; severity?: string; participants?: string[]; auto_generate?: boolean }) {
  return fetchJson<Simulation>("/api/v1/simulations/", { method: "POST", body: JSON.stringify(payload) });
}

export async function startSimulation(id: string) {
  return fetchJson<Simulation>(`/api/v1/simulations/${id}/start`, { method: "POST" });
}

export async function respondSimulation(id: string, operator_notes: string) {
  return fetchJson<Simulation>(`/api/v1/simulations/${id}/respond`, { method: "POST", body: JSON.stringify({ operator_notes }) });
}

export async function evaluateSimulation(id: string) {
  return fetchJson<{ summary: string; score: number; breakdown: SimulationBreakdownItem[] }>(`/api/v1/simulations/${id}/evaluate`, { method: "POST" });
}

export async function deleteSimulation(id: string) {
  return fetchJson<void>(`/api/v1/simulations/${id}`, { method: "DELETE" });
}

// ─── P2.2 Continuity activation ────────────────────────────────────────────
export type ActivationStatus = "pending" | "activated" | "failed" | "cancelled";

export interface ContinuityActivation {
  id: string;
  crisis_id: string;
  bcp_plan_id: string | null;
  bcp_plan_name: string | null;
  status: ActivationStatus;
  provider: string;
  request_payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  error_message: string | null;
  activated_at: string | null;
  created_at: string;
  updated_at: string;
}

export async function activateBCP(crisisId: string, payload: { bcp_plan_id?: string; bcp_plan_name?: string; notes?: string }) {
  return fetchJson<ContinuityActivation>(`/api/v1/crisis/${crisisId}/activate-bcp`, { method: "POST", body: JSON.stringify(payload) });
}

export async function listActivations(crisisId: string) {
  return fetchJson<ContinuityActivation[]>(`/api/v1/crisis/${crisisId}/activations`);
}

// ─── P2.3 Media monitoring ─────────────────────────────────────────────────
export interface MediaMention {
  id: string;
  outlet: string;
  url: string | null;
  headline: string | null;
  snippet: string;
  author: string | null;
  sentiment: Sentiment | null;
  sentiment_score: number | null;
  key_themes: string[];
  analyzed_at: string | null;
  crisis_id: string | null;
  mentioned_at: string;
  created_at: string;
  updated_at: string;
}

export interface MediaCoverage {
  crisis_id: string;
  total_mentions: number;
  analyzed_count: number;
  counts: { positive: number; neutral: number; negative: number; mixed: number };
  average_score: number | null;
  top_themes: string[];
  by_outlet: Record<string, number>;
  mentions: MediaMention[];
}

export async function listMediaMentions(params?: { crisis_id?: string }) {
  const q = new URLSearchParams();
  if (params?.crisis_id) q.set("crisis_id", params.crisis_id);
  return fetchJson<MediaMention[]>(`/api/v1/media-mentions/?${q.toString()}`);
}

export async function createMediaMention(payload: { outlet: string; snippet: string; url?: string; headline?: string; author?: string; crisis_id?: string; auto_analyze?: boolean }) {
  return fetchJson<MediaMention>("/api/v1/media-mentions/", { method: "POST", body: JSON.stringify(payload) });
}

export async function analyzeMediaMention(id: string) {
  return fetchJson<MediaMention>(`/api/v1/media-mentions/${id}/analyze`, { method: "POST" });
}

export async function deleteMediaMention(id: string) {
  return fetchJson<void>(`/api/v1/media-mentions/${id}`, { method: "DELETE" });
}

export async function getMediaCoverage(crisisId: string) {
  return fetchJson<MediaCoverage>(`/api/v1/media-mentions/coverage/${crisisId}`);
}

// ─── P2.4 Legal Hold ───────────────────────────────────────────────────────
export type LegalHoldStatus = "draft" | "active" | "released";

export interface LegalHoldCustodian {
  name?: string;
  email?: string;
  role?: string;
}

export interface LegalHold {
  id: string;
  crisis_id: string | null;
  title: string;
  scope_description: string | null;
  custodians: LegalHoldCustodian[];
  data_sources: string[];
  hold_notice_text: string | null;
  status: LegalHoldStatus;
  issued_at: string | null;
  released_at: string | null;
  issued_by: string | null;
  release_reason: string | null;
  created_at: string;
  updated_at: string;
}

export async function listLegalHolds(params?: { crisis_id?: string; active_only?: boolean }) {
  const q = new URLSearchParams();
  if (params?.crisis_id) q.set("crisis_id", params.crisis_id);
  if (params?.active_only) q.set("active_only", "true");
  return fetchJson<LegalHold[]>(`/api/v1/legal-holds/?${q.toString()}`);
}

export async function createLegalHold(payload: { crisis_id?: string; title: string; scope_description?: string; custodians?: LegalHoldCustodian[]; data_sources?: string[]; hold_notice_text?: string; issued_by?: string }) {
  return fetchJson<LegalHold>("/api/v1/legal-holds/", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateLegalHold(id: string, payload: Partial<Omit<LegalHold, "id" | "created_at" | "updated_at" | "status" | "issued_at" | "released_at" | "release_reason">>) {
  return fetchJson<LegalHold>(`/api/v1/legal-holds/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function issueLegalHold(id: string) {
  return fetchJson<LegalHold>(`/api/v1/legal-holds/${id}/issue`, { method: "POST" });
}

export async function releaseLegalHold(id: string, reason?: string) {
  return fetchJson<LegalHold>(`/api/v1/legal-holds/${id}/release`, { method: "POST", body: JSON.stringify({ reason }) });
}

export async function deleteLegalHold(id: string) {
  return fetchJson<void>(`/api/v1/legal-holds/${id}`, { method: "DELETE" });
}

export async function draftHoldNotice(crisisId: string) {
  return fetchJson<{ notice_text: string }>(`/api/v1/crisis/${crisisId}/draft-hold-notice`, { method: "POST" });
}

export interface EvidenceRecommendation {
  data_sources: { name: string; type: string; rationale: string }[];
  custodians: { role: string; reason: string }[];
  preservation_duration_days_min: number;
}

export async function recommendEvidence(crisisId: string) {
  return fetchJson<EvidenceRecommendation>(`/api/v1/crisis/${crisisId}/recommend-evidence`, { method: "POST" });
}

// ─── Demo data (landing page seeder) ──────────────────────────────────────
export interface DemoCounts {
  crises: number;
  team_members: number;
  stakeholders: number;
  resources: number;
  signals: number;
  simulations: number;
  legal_holds: number;
  media_mentions: number;
}

export interface DemoStatus {
  seeded: boolean;
  counts: DemoCounts;
}

export async function getDemoStatus() {
  return fetchJson<DemoStatus>("/api/v1/demo/status");
}

export async function seedDemo() {
  return fetchJson<DemoCounts & { created: number; skipped: number | string }>(
    "/api/v1/demo/seed",
    { method: "POST" },
  );
}

export async function clearDemo() {
  return fetchJson<Record<string, number>>("/api/v1/demo/clear", { method: "POST" });
}

export { ApiError };
