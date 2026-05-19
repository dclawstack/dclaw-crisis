---
tags: [meta, prd, revised, swarm]
version: 2.8
date: 2026-05-19
app_id: crisis
app_name: DClaw Crisis
category: Operations
status: Active
---

# 📘 DClaw Crisis — Revised PRD v2.8

> **The single document every agent must read before writing code for this app.**
> Generated from DClaw Master PRD v2.2. Read the Master PRD first: https://raw.githubusercontent.com/dclawstack/dclaw-prd/main/DClaw-Master-PRD.md

---

## 1. Product Identity

| Field | Value |
|-------|-------|
| **App ID** | `crisis` |
| **Name** | DClaw Crisis |
| **Category** | Operations |
| **Tagline** | Crisis response |
| **Color** | #EC4899 |
| **Phase** | Future |
| **Port (Frontend Dev)** | 3079 (assigned) |
| **Port (Backend Dev)** | 18149 (assigned) |
| **Maturity Tier** | 🟢 Tier 3 — Production-Ready Foundation |

---

## 2. Current State Assessment

### 2.1 Scaffold Status
| Component | Status | Notes |
|-----------|--------|-------|
| `frontend/` | ✅ | Next.js 14+ app |
| `backend/` | ✅ | FastAPI + SQLAlchemy 2.0 |
| `docs/` | ✅ | getting-started, guides, reference, releases |
| `helm/` | ✅ | K8s deployment manifests |
| `.github/workflows/` | ✅ | CI/CD + Claude integration |
| `AGENTS.md` | ✅ | Per-repo agent instructions |
| `PLAN-v1.2.md` | ✅ | Feature roadmap |
| `docker-compose.yml` | ✅ | Local dev stack |
| `tests/` | ✅ | pytest + pytest-asyncio |
| `alembic/` | ✅ | Database migrations |
| `dclaw-manifest.json` | ✅ | `frontend/public/dclaw-manifest.json` shipped |

### 2.2 Code Maturity
| Metric | Value |
|--------|-------|
| Python source files (backend) | ~37 |
| TypeScript/TSX files (frontend) | ~18 |
| Total source files | ~55 |
| Tests | ✅ 34 passing |
| Alembic migrations | ✅ Present |
| DPanel manifest | ✅ Present |
| LLM provider integration | ✅ OpenRouter + Ollama fallback |
| AI Copilot UI | ✅ Floating chat on every route |

### 2.3 Feature Maturity
- **P0 Foundation:** ✅ Fully implemented (Copilot, Detection, Response Planning at 20 templates + AI customization, Command Center with Situation Map).
- **P1 Platform:** ✅ Fully shipped — Communication Management (drafting + multi-channel send-out + AI sentiment), Stakeholder Mapping, Resource Mobilization, Post-Crisis Review.
- **P2 Vertical:** Not yet started

---

## 3. Gap Analysis

| # | Gap | Severity | Status | Fix |
|---|-----|----------|--------|-----|
| 1 | Missing `dclaw-manifest.json` | 🔴 | ✅ Closed | `frontend/public/dclaw-manifest.json` added |
| 2 | No AI Copilot (YC mandate §9) | 🔴 | ✅ Closed | `services/copilot.py` + `services/llm.py` + `components/Copilot.tsx` |
| 3 | No AI summarizer / recommender / comm draft | 🟡 | ✅ Closed | Endpoints under `/api/v1/crisis/{id}/summarize`, `/next-action`, `/communications/draft` |
| 4 | No response plan templates (P0.3) | 🟡 | ✅ Closed | 5 seeded playbooks + `POST /playbooks/{id}/instantiate` |
| 5 | Command Center lacks resource view + decision support | 🟡 | ✅ Closed | Dashboard now polls every 15s, shows team availability + AI recommendation for top-severity active crisis |
| 6 | Crisis Detection (P0.2) | 🟡 | ✅ Closed | Signal ingestion contract + AI scoring shipped (`/api/v1/signals/`); see §14. Pollers for real sources (RSS/social/news) deferred to integration work. |
| 7 | Stakeholder Mapping (P1.2) | 🟡 | ⏳ Pending | v1.4 candidate |
| 8 | Resource Mobilization (P1.3) | 🟡 | ⏳ Pending | v1.4 candidate |
| 9 | Post-Crisis Review (P1.4) | 🟡 | ⏳ Pending | v1.4 candidate — AI lessons-extraction over resolved crises |

---

## 4. Sacred Architecture & Tech Stack

> **NON-NEGOTIABLE. Every DClaw product MUST use this exact stack.**

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | Next.js 14+ | App Router, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI | Pydantic v2, SQLAlchemy 2.0, asyncpg |
| **Database** | PostgreSQL 16 | CloudNativePG operator in K8s |
| **Vector DB** | Qdrant / pgvector | Only if RAG / semantic search |
| **Cache / Bus** | Redis | 7.x |
| **Object Storage** | MinIO | Latest |
| **Workflow** | Temporal.io | Only if automation/orchestration |
| **Auth** | Logto | JWT validation on all protected routes |
| **Billing** | Stripe | Metered or per-seat |
| **K8s Operator** | Go + controller-runtime | 0.18 |
| **LLM Local** | Ollama | Apple Silicon |
| **LLM Cloud** | OpenRouter + Kimi K2.5 | Fallback |
| **Monitoring** | Prometheus + Grafana | Latest |

### 4.1 Python Rules
- `ruff` formatting enforced
- Type hints on ALL public APIs
- `pydantic` v2 for schemas
- `sqlalchemy` 2.0 style (`Mapped`, `mapped_column`)
- `pytest` + `pytest-asyncio` for tests
- Functions < 50 lines
- No `print()` — use `structlog`

### 4.2 TypeScript / Next.js Rules
- Strict TypeScript (`strict: true`)
- Tailwind for ALL styling
- `cn()` utility for conditional classes
- No `any` without `// @ts-ignore`

### 4.3 Docker Standards
- Port mappings MUST match container listen port
- Healthchecks MUST use binaries present in base image
- `docker compose config` must pass before shipping
- Service type MUST be `ClusterIP`
- TLS required on all ingress

---

## 5. P0 Foundation Features (Must Have — Demo Ready)

> **Every P0 MUST include an AI Copilot per YC S25/W26 RFS.**

| # | Feature | Status | Description | AI Component | Acceptance Criteria |
|---|---------|--------|-------------|--------------|---------------------|
| P0.1 | **AI Crisis Copilot** | ✅ Shipped | Detect crises, orchestrate response, and manage communications. | LLM crisis-detection + response-orchestration + communication-drafting | Floating chat on every route; per-crisis Summarize / Next-Action / Draft-Comm endpoints; OpenRouter primary, Ollama fallback |
| P0.2 | **Crisis Detection** | ✅ Shipped (v1) | Ingest signals from any source and AI-triage them before they become full crises. | AI signal-detection + severity-scoring + early-warning | Open ingestion contract (`POST /signals/`) any webhook/monitor can call; AI scores severity/category/confidence on ingest; flags `ai_recommends_promotion`; human always approves promotion to Crisis. Real source pollers (RSS, social, news) are integration follow-ups against this contract. |
| P0.3 | **Response Planning** | ✅ Shipped | Pre-built crisis response plans, instantiable to a live crisis with action items, with optional AI customization to the specific incident. | AI plan-customization + resource-allocation | 20 seeded templates; `POST /playbooks/{id}/instantiate` accepts `incident_context` → AI rewrites each step for the specific incident. |
| P0.4 | **Command Center** | ✅ Shipped | Real-time crisis dashboard with situation map, resource availability, and AI decision support. | AI situation-awareness + resource-optimization | Situation Map (severity rows × active crises with age, action progress, escalation flag for stale critical >1h); 15s polling refresh; team availability by department; AI recommendation for top-severity active crisis. |

---

## 6. P1 Platform Features (Should Have — v1.1–1.2)

| # | Feature | Status | Description | AI Component | Acceptance Criteria |
|---|---------|--------|-------------|--------------|---------------------|
| P1.1 | **Communication Management** | ✅ Shipped | Draft, send via channel adapters, and monitor predicted-audience-sentiment over time. | AI communication-drafting + channel-optimization + sentiment-monitoring | AI drafting <2 min via `/communications/draft`. Channel adapters (email/slack/sms/app) via simulator-pattern dispatch with `POST /communications/{id}/send`. Sentiment analyzer predicts audience reaction + risk flags via `POST /communications/{id}/analyze-sentiment`. Per-crisis aggregated trend via `GET /crisis/{id}/sentiment-trend`. UI: send button on draft comms, sentiment badge + risk flags inline, sentiment trend sparkline card on crisis detail page. |
| P1.2 | **Stakeholder Mapping** | ✅ Shipped | Track internal and external stakeholders; AI ranks who to contact, when, through what channel, with talking points. | AI stakeholder-prioritization + communication-timing | `Stakeholder` model (type, importance, contact, tags). `GET /crisis/{id}/stakeholder-priorities` returns ranked list with urgency (immediate / within_4h / within_24h / post_resolution), channel, talking_points, rationale. UI: `/stakeholders` table + per-crisis "Stakeholder priorities" button. |
| P1.3 | **Resource Mobilization** | ✅ Shipped | Track war rooms, comm channels, vendor contacts, equipment, budget pools; AI matches resources to crisis needs and flags conflicts. | AI resource-matching + deployment-optimization | `Resource` model (type, status, capacity, location, attributes JSON). `GET /crisis/{id}/recommend-resources` returns fit-scored recs sorted desc, with conflict_note for in-use items and `gaps[]` for missing capabilities. UI: `/resources` 4-status kanban + per-crisis "Recommend resources" button. |
| P1.4 | **Post-Crisis Review** | ✅ Shipped | Generate a structured AI post-mortem and suggest playbook updates from any crisis. | AI lessons-extraction + plan-update-suggestion | `POST /crisis/{id}/post-mortem` → {timeline_summary, what_went_well, what_went_poorly, root_cause, lessons_learned, is_speculative}. `POST /crisis/{id}/suggest-playbook-updates` → ranked suggestions (add/rewrite/remove/change_role) against the closest-category playbook. Never auto-applies. |

---

## 7. P2 Vertical / Scale Features (Could Have — v1.3+)

| # | Feature | Description | AI Component | Acceptance Criteria |
|---|---------|-------------|--------------|---------------------|
| P2.1 | **Simulation & Training** | Run crisis simulations with AI-generated scenarios. | AI scenario-generation + participant-evaluation | Generate scenarios; run simulation; evaluate response; score |
| P2.2 | **Integration with Continuity** | Sync with DClaw Continuity for BCP activation. | API sync + plan-activation | Auto-activate BCP; sync status; unified reporting |
| P2.3 | **Media Monitoring** | Track media coverage and sentiment during crisis. | AI media-monitoring + sentiment-analysis + response-suggestion | Track 1000 outlets; sentiment score; suggest responses |
| P2.4 | **Legal Hold** | Manage legal hold and evidence preservation during crisis. | AI legal-hold-management + evidence-tracking | Issue legal hold; track compliance; preserve evidence |

---

## 8. Scaffold Checklist

Before marking this app "shipped", confirm:

- [x] `frontend/` with Next.js 14+, Tailwind, pre-built UI components
- [x] `backend/` with FastAPI, Pydantic v2, SQLAlchemy 2.0, asyncpg
- [x] `docs/` with getting-started, guides, reference, releases, troubleshooting
- [x] `helm/` with Chart.yaml, values.yaml, templates (deployment, service, ingress, cloudnativepg)
- [x] `.github/workflows/` with build-backend.yml, build-frontend.yml, deploy.yml, claude.yml
- [x] `frontend/public/dclaw-manifest.json` for DPanel registration
- [x] `backend/tests/` with pytest + pytest-asyncio
- [x] `backend/alembic/` with initial migration
- [x] `Dockerfile` + `docker-compose.yml` with correct healthchecks
- [x] Health endpoint at `/health` returning `{"status":"ok"}`
- [x] `AGENTS.md` with per-repo instructions
- [x] `PLAN-v1.2.md` with feature roadmap
- [x] Port assigned from registry and documented (`18149` backend / `3079` frontend)
- [x] No hardcoded secrets — use `.env.example` + K8s Secrets
- [x] Non-root containers in Dockerfile

---

## 9. AI Copilot Mandate (YC S25/W26 Requirement)

Every DClaw app MUST have an AI Copilot as its first P0 feature. The copilot must:
1. ✅ Be contextually aware of the app's domain data — `services/copilot.py` loads active crises, open actions, focused crisis snapshot
2. 🟡 Use RAG over the app's knowledge base where applicable — direct DB context today; vector search deferred to v1.4
3. ✅ Suggest next actions, not just answer questions — `/crisis/{id}/next-action` + Copilot system prompt
4. ✅ Be accessible from every page via floating chat or sidebar — `<Copilot />` in root layout
5. ✅ Fall back to local Ollama when cloud is unavailable — `services/llm.py` tries OpenRouter first, then Ollama

---

## 10. Next Tasks for Vibe Coders

1. **P2.1 Simulation & Training** — AI-generated tabletop scenarios.
2. **P2.3 Media Monitoring** — sentiment tracking across configured outlets (distinct from P1.1 which predicts reaction to our outbound comms).
3. **P2.2 Continuity Integration** — sync resolved crises with DClaw Continuity for BCP activation.
4. **P2.4 Legal Hold** — evidence preservation workflow during active crises.
5. **Real channel provider integrations** — replace simulator adapters with SendGrid/SES (email), Slack Web API or Incoming Webhooks, Twilio (SMS).
6. **First real signal source integration** — RSS poller (or webhook adapter) that posts to `/api/v1/signals/`.
7. **Playbook advisor → one-click apply** — accept individual `suggested_changes` and write them back to the playbook (with audit trail).
8. **Stakeholder communication scheduling** — schedule follow-ups per stakeholder per crisis.
9. **Resource reservation** — `deploy_now` recommendations get a click-to-reserve that flips status to `in_use` with a crisis link.

---

## 11. Domain Research Notes

Inspired by Crisp, Dataminr, Everbridge, OnSolve. AI crisis management minimizes damage and recovery time.

---

## 12. Links & Resources

| Resource | URL |
|----------|-----|
| **Master PRD** | https://raw.githubusercontent.com/dclawstack/dclaw-prd/main/DClaw-Master-PRD.md |
| **GitHub Org** | https://github.com/dclawstack |
| **DPanel** | https://dpanel.dclawstack.io |
| **Port Registry** | See `dclaw-platform/PORT_REGISTRY.md` |
| **App PRD Template** | Obsidian Vault → `00-META/📐 App PRD Template.md` |
| **Scaffold Source** | `dclaw-scaffold/` in DClaw-Stack |

---

---

## 13. v1.3 Implementation Notes (2026-05-18)

This release closes the foundational gaps identified in v2.3 of this PRD. Summary of work:

**Backend additions**
- `app/services/llm.py` — unified LLM client (OpenRouter primary, Ollama fallback, 503 on failure)
- `app/services/crisis_context.py` — prompt-ready snapshot of a crisis + actions + recent comms
- `app/services/ai_summarizer.py`, `ai_recommender.py`, `ai_comm_draft.py` — single-purpose AI services
- `app/services/copilot.py` — context-loading chat function (active crises, open actions, focused snapshot)
- `app/services/playbook_seed.py` — 5 seeded response-plan templates
- New endpoints: `POST /api/v1/copilot/chat`, `POST /api/v1/crisis/{id}/summarize`, `GET /api/v1/crisis/{id}/next-action`, `POST /api/v1/communications/draft`, `POST /api/v1/playbooks/seed`, `POST /api/v1/playbooks/{id}/instantiate`
- 12 new tests (`test_ai.py`, additions to `test_playbooks.py`) — full suite: **34 passing**

**Frontend additions**
- `src/components/Copilot.tsx` — floating chat panel, mounted in root layout, auto-detects crisis focus from URL
- Crisis detail page: AI Tools card with Summarize / Next Action buttons; AI Draft button in comm modal
- Dashboard upgrades: 15s polling refresh, team availability panel, AI decision-support card for top-severity active crisis
- Playbooks page: "Seed Templates" + per-template "Use Template" instantiation flow
- `frontend/public/dclaw-manifest.json` — DPanel registration

**Infra changes**
- Ports migrated `8061 → 18149` (backend) and `3061 → 3079` (frontend) per PRD §1
- `app/core/config.py` — added LLM provider settings (OpenRouter URL/model/key, Ollama URL/model)

**Explicit deferrals**
- **RAG / vector search** for the Copilot — current context loader pulls structured DB rows, not embeddings. pgvector or Qdrant can be layered in once we have crisis post-mortems and playbook docs worth indexing.
- **Real-time situation map** — dashboard polls every 15s today; WebSocket/SSE upgrade is in PLAN-v1.2 P2.7.

---

## 14. P0.2 Crisis Detection — design notes (2026-05-18)

The PRD originally framed P0.2 as "monitor 1000 sources." That number is aspirational and the wrong unit of work — building 1000 source-specific scrapers is integration work that scales by the source, not by core platform value. Instead, this release ships the platform-side contract and AI triage pipeline; specific source pollers can then be added incrementally without touching the core.

**Architecture**
- `Signal` model (`backend/app/models/signal.py`): immutable record of one observation, with optional `crisis_id` link if it was promoted.
- `POST /api/v1/signals/` is the universal ingestion endpoint — any integration (RSS poller, Slack bot, Datadog webhook, manual entry, internal alert) posts the same payload.
- `services/ai_signal_scorer.py` runs synchronously on ingest by default and returns `{severity, category, confidence, summary, rationale, is_crisis}`. The scorer is conservative on severity by system prompt and clamps confidence + falls back to safe defaults if the model strays from the schema.
- `ai_recommends_promotion` is set only when `is_crisis=true`, severity is `high`/`critical`, **and** confidence ≥ 0.6 — flagged visually in the UI but **never auto-promotes**. Crisis declaration always requires a human click.

**Operator UI**
- `/signals` is a 4-column kanban: New → Triaged → Promoted / Dismissed. Auto-refreshes every 15s. Recommended-for-promotion signals are highlighted with a pink border so they stand out in the "New" column.
- One-click `Promote` creates a Crisis (with AI-derived defaults overrideable on the spot) and links the originating Signal.

**What is intentionally NOT in v1**
- No real source pollers (RSS, social, news, status pages). The contract is ready; pollers are integration work that lives outside the core repo or in isolated workers.
- No deduplication. Two near-identical signals from the same source become two rows. The Next Tasks list calls this out.
- No background scoring queue. Scoring is inline on ingest; ingestion latency = LLM round-trip (~1-3s for Kimi K2). If volume grows, swap to a Temporal workflow.
- No alerting/paging on `ai_recommends_promotion=true`. The dashboard surfaces it; downstream notification routing is out of scope.

**Tests**: 12 new (`tests/test_signals.py`), mocked LLM. Full suite: **46 passing**.

---

---

## 15. P0 polish + P1.4 — design notes (2026-05-18)

This release completes the remaining P0 polish items and ships P1.4 Post-Crisis Review.

**P0.3 → 20 templates + AI customization**
- `playbook_seed.py` expanded from 5 → 20 templates covering: ransomware, cloud provider outage, key personnel departure, regulatory inquiry, product recall, GDPR/CCPA DSAR, third-party vendor failure, DDoS, phishing/BEC, financial fraud, IP theft, executive impersonation/deepfake, insider threat, natural disaster, pandemic.
- `services/ai_playbook_customizer.py` rewrites each step's title/description for a specific incident when the operator provides `incident_context` on instantiate. Roles and step counts are preserved (the model can't add or drop steps). Falls back to generic steps if the LLM call fails — the response shape includes `ai_customized: bool` so the UI can show whether AI was used.
- **Breaking API change**: `POST /playbooks/{id}/instantiate` now returns `{crisis, ai_customized}` instead of `CrisisResponse` directly. Tests + frontend updated.

**P0.4 → Situation Map**
- New `SituationMap` component above the existing dashboard cards. Renders all active crises (detected/assessing/responding) as cards in a 4-row grid by severity. Each card shows status, category, age, and action-item progress bar. Cards turn red when severity=critical AND age > 1 hour (escalation indicator). Header chips summarize the critical/high counts and stale-critical count for at-a-glance situational awareness.
- Polling cadence (15s) shared with the rest of the dashboard.

**P1.4 → Post-Crisis Review**
- `services/ai_post_mortem.py` returns a structured post-mortem: timeline summary, what-went-well, what-went-poorly, root cause, lessons-learned, `is_speculative` flag for thin-context cases. Safe shaping: every list field is normalized via `_as_list` so malformed AI output doesn't break the response model.
- `services/ai_playbook_advisor.py` finds the closest-category playbook and suggests concrete changes — add/rewrite/remove step or change role — each with a rationale. **Never auto-applies.** The frontend renders suggestions as cards; a future PR will add one-click "Apply this change" with an audit trail.
- Endpoints live under `POST /crisis/{id}/post-mortem` and `POST /crisis/{id}/suggest-playbook-updates`. Both work on any crisis status but the UI nudges the operator to use them on resolved/contained crises where context is richer.

**Tests**: 52 passing (10 new, covering post-mortem 200/404, advisor with/without matching playbook, AI customization with/without context, junk-entry filtering).

---

---

## 16. P1.2 + P1.3 — design notes (2026-05-18)

**Distinction from existing models**
- `TeamMember` = *internal responders* (the people doing the work).
- `Stakeholder` = *external + internal audiences* you communicate **with** during a crisis (customers, regulators, media, investors, board, vendors, partners).
- `Resource` = *non-people assets* you deploy: war rooms, Slack channels, vendor contacts, equipment, budget pools, on-call rosters, external services.

This separation matters because each maps to a different AI workflow: TeamMembers get *assigned* action items, Stakeholders get *contacted*, Resources get *deployed*.

**AI design conservatism**
- Stakeholder prioritizer filters out anything tagged `not_required` and unknown IDs; sorts results by urgency in code (not trusting model order).
- Resource matcher enforces `fit_score >= 0.3` to avoid noise; respects in-use status by surfacing a `conflict_note` rather than blocking the recommendation; reports `gaps[]` for missing capabilities so the operator knows the org needs new resources, not just better matching.
- Empty-roster / empty-inventory cases short-circuit before calling the LLM and return helpful guidance instead of an error.

**Endpoints**
- `GET /api/v1/stakeholders/` `POST /` `GET/PUT/DELETE /{id}` — CRUD with optional `type` and `active_only` filters.
- `GET /api/v1/resources/` `POST /` `GET/PUT/DELETE /{id}` — CRUD with optional `status` and `resource_type` filters.
- `GET /api/v1/crisis/{id}/stakeholder-priorities` — AI ranking.
- `GET /api/v1/crisis/{id}/recommend-resources` — AI matching with gaps.

**UI**
- `/stakeholders` — table with type filter, active-only toggle, edit modal with tags + notes.
- `/resources` — 4-column kanban grouped by status (available / reserved / in use / unavailable), cards show capacity + location + free-form JSON attributes.
- Crisis detail page: two more AI buttons surface results inline with structured rendering (urgency-colored badges, talking points, fit-score progress, gap list).

**Tests**: 64 passing (12 new — stakeholder + resource CRUD + filter tests, prioritizer and matcher endpoint tests with junk-entry filtering and empty-roster paths).

---

---

## 17. P1.1 Phase 2 — design notes (2026-05-19)

Closes the last open P1 feature. PRD §6 P1.1 was "draft + distribute + monitor sentiment" — drafting shipped earlier; this release covers distribution and sentiment.

**Channel adapters (simulator pattern)**
- `services/channels/{email,slack,sms,app}.py` each implement a tiny `ChannelAdapter` protocol (`async def send(comm) -> DeliveryReceipt`). In simulator mode they log the payload and return a structured receipt (provider, sent_at_iso, channel-specific details — SMS counts segments, Slack hints a channel, email hints a subject).
- `services/channels/dispatcher.py` picks the adapter by `comm.channel`. Swap any one for a real provider (SendGrid, Slack webhook, Twilio) without touching the endpoint code or the data model.

**Sentiment ≠ media monitoring**
- This P1.1 feature analyzes the *outbound* message and predicts how the audience will receive it (predicted reaction + risk flags like "tone too defensive", "no fix timeline"). It's a content-quality check.
- *External* sentiment over media outlets / social platforms is P2.3 Media Monitoring, intentionally a separate capability.

**Data model additions** (alembic `2ffe0f8ef9a7`)
- `delivery_status` (pending/queued/sent/failed), `sent_at`, `delivery_log` (JSON receipt from the adapter).
- `sentiment` + `sentiment_score` (−1..+1) + `sentiment_analyzed_at` + `predicted_reaction` + `risk_flags` (JSON list).
- Server defaults on NOT NULL columns so the migration backfills cleanly on a live table.

**Endpoints**
- `POST /api/v1/communications/{id}/send` — calls the channel dispatcher, persists `sent_at` + `delivery_log`. Returns 400 if already sent or unknown channel; 502 if the adapter raises.
- `POST /api/v1/communications/{id}/analyze-sentiment` — runs the analyzer, persists fields. Returns 503 if no LLM provider.
- `GET /api/v1/crisis/{id}/sentiment-trend` — aggregated timeline: counts by sentiment, average score, `trend_direction` (improving / worsening / flat / insufficient_data), ordered points for sparkline rendering.

**UI**
- Communication rows: status badge (Draft / Sent / Failed), sentiment badge + score, predicted reaction, risk-flag callout, Send button (auto-hides once sent), Analyze button.
- Crisis detail: new "Sentiment Trend" card with trend direction + sparkline; only visible when at least one comm exists.

**Tests**: 12 new — channel adapter dispatch (parametrized over all 4 channels), already-sent 400, send 404, sentiment persistence (positive + negative paths), risk-flag aggregation, trend aggregation with mixed positive/negative comms + an unanalyzed comm, empty trend, 404. Full suite: **76 passing**.

---

*Revised PRD version: 2.8*
*Updated: 2026-05-19 — P0 + P1 both fully shipped*
*Next review: When the first P2 feature lands*
