---
tags: [meta, prd, revised, swarm]
version: 2.5
date: 2026-05-18
app_id: crisis
app_name: DClaw Crisis
category: Operations
status: Active
---

# 📘 DClaw Crisis — Revised PRD v2.5

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
- **P0 Foundation:** ✅ Fully implemented (Copilot, Detection, Response Planning, Command Center).
- **P1 Platform:** 🟡 Communication Management partially shipped (AI drafting + multi-type/channel). Stakeholder mapping, resource mobilization, post-crisis review still pending.
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
| P0.3 | **Response Planning** | ✅ Shipped (v1) | Pre-built crisis response plans, instantiable to a live crisis with action items. | AI plan-customization + resource-allocation | 5 seeded templates; `POST /playbooks/{id}/instantiate` → new Crisis + action items. Target: 20 templates + AI customization in v1.4 |
| P0.4 | **Command Center** | ✅ Shipped (v1) | Real-time crisis dashboard with resource availability and AI decision support. | AI situation-awareness + resource-optimization | 15s polling refresh; team availability by department; AI recommendation for top-severity active crisis. Target: situation map in v1.4 |

---

## 6. P1 Platform Features (Should Have — v1.1–1.2)

| # | Feature | Status | Description | AI Component | Acceptance Criteria |
|---|---------|--------|-------------|--------------|---------------------|
| P1.1 | **Communication Management** | 🟡 Partial | Draft and distribute crisis communications across channels. | AI communication-drafting + channel-optimization + sentiment-monitoring | ✅ AI drafting in <2 min via `/communications/draft`. ⏳ Channel send-out and sentiment monitoring pending |
| P1.2 | **Stakeholder Mapping** | ⏳ Pending | Track and communicate with internal and external stakeholders. | AI stakeholder-prioritization + communication-timing | Map 100 stakeholders; prioritize; schedule communications |
| P1.3 | **Resource Mobilization** | ⏳ Pending | Track and deploy resources during crisis response. | AI resource-matching + deployment-optimization | Track 50 resource types; match to need; optimize deployment |
| P1.4 | **Post-Crisis Review** | ⏳ Pending | Document lessons learned and update plans. | AI lessons-extraction + plan-update-suggestion | Extract 10 lessons; suggest plan updates; track implementation |

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

1. **First real source integration** — build an RSS poller (or a Slack/Datadog webhook adapter) that posts to `/api/v1/signals/`. Demonstrates the ingestion contract end-to-end against a live feed.
2. **Stakeholder Mapping (P1.2)** — new model + page; AI prioritization scoring.
3. **Post-Crisis Review (P1.4)** — extend resolved-crisis flow with AI lessons-extraction and playbook-update suggestions.
4. **Expand response-plan templates** from 5 → 20, and add AI auto-customization at instantiation time.
5. **Signal deduplication** — when the same source emits near-identical raw_text within N minutes, merge into the existing Signal row instead of creating a duplicate.

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

*Revised PRD version: 2.5*
*Updated: 2026-05-18 — P0.2 Crisis Detection shipped*
*Next review: After first real source integration ships against the `/signals` contract*
