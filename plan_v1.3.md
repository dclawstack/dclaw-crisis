# DClaw Crisis — Strategic Plan v1.3

## YC-Level Vision & Product Thesis

**DClaw Crisis** is an AI-native Crisis & Incident Command Center. While technical teams have PagerDuty and Datadog, business operations, legal, HR, and PR teams have zero dedicated tooling when a crisis hits. Companies lose millions per hour during mismanaged incidents — not from the incident itself, but from the chaos of coordination.

### The "Hair-on-Fire" Problem

During a business crisis (supply chain disruption, product recall, PR disaster, regulatory action, cyber breach, M&A disruption):

- **40% of response time is lost to coordination** — finding the right stakeholders, routing updates, tracking action items across Slack threads and spreadsheets.
- **Average incident cost for enterprise: $300K–$1M per hour.**
- **Current tools are developer-only.** PagerDuty, Opsgenie, and ServiceNow ITSM serve SREs. Business crisis teams use email chains and Google Docs.
- **No AI copilot exists** for non-technical incident command. No tool suggests next actions, auto-drafts stakeholder comms, or predicts escalation timelines.

### Why This Wins at YC

| YC Criteria | How DClaw Crisis Delivers |
|-------------|---------------------------|
| **Solves a real problem** | Every Fortune 1000 has an under-equipped crisis management function |
| **Large/ growing market** | $8.7B incident management market, 21% CAGR |
| **Defensible moat** | AI playbook engine gets smarter with every crisis; network effects from org-specific playbooks |
| **Rapid execution path** | Clear v1.0 → v1.2 → v1.3 feature maps; can demo in weeks |
| **Clear monetization** | Seat-based SaaS + enterprise playbook customization |

### Competitive Landscape

| Competitor | Weakness | Our Advantage |
|------------|----------|---------------|
| **PagerDuty** | Developer-only; no business/ops workflow | Built for ops, legal, PR, HR — any team |
| **ServiceNow ITSM** | Bloated, IT-ticket-centric, $$$ | Lightweight, crisis-native, affordable |
| **rutube (ex-Samanage)** | Missing AI; generic helpdesk feel | AI copilot + playbook engine |
| **Spreadsheets + Slack** | 40% coordination overhead | Purpose-built crisis command workflows |

---

## Current State Audit

### What Exists Today

The repository is in **raw scaffold state** — virtually all templates are uncustomized:

| Component | Status | Issue |
|-----------|--------|-------|
| `PRODUCT-SPEC.md` | ❌ Stale CRM template | Still references Customer/Deal/Activity CRM entities; never updated for "Crisis" domain |
| `AGENTS.md` | ⚠️ Partially customized | App identity set to DClaw Crisis, ports `8061/3061`, but port registry in README is stale |
| `docker-compose.yml` | ❌ Wrong ports | Uses `8151/3065` not matching `AGENTS.md` (`8061/3061`) |
| Backend models | ❌ Empty | Only `Base` model exists |
| Backend schemas | ❌ Empty | Only `__init__.py` |
| Backend repositories | ❌ Empty | Only `BaseRepository` exists |
| Backend routers (v1) | ❌ Empty | Only `__init__.py` |
| Backend tests | ⚠️ Skeleton | Only `test_health.py` passes |
| Frontend pages | ❌ Placeholder | Only `page.tsx` with "DClaw App" placeholder |
| Frontend API client | ⚠️ Skeleton | Only `getHealth()` function |
| Alembic migrations | ❌ None | No migrations generated |
| Helm charts | ⚠️ Scaffold | Not customized for Crisis app |

### Critical Fixes Required Before Any Feature Work

1. **Align ports**: `docker-compose.yml` backend → `8061`, frontend → `3061`
2. **Update `frontend/package.json`**: Port in dev script → `3061`
3. **Update `config.py`**: `database_url` → `dclaw_crisis`, `app_name` → "DClaw Crisis"
4. **Update `AGENTS.md` / README port registry**: Add `dclaw-crisis` entry
5. **Replace `PRODUCT-SPEC.md`** with Crisis Management domain model

---

## Domain Model: Crisis Management

### Core Entities

```
Crisis
├── id: UUID (PK)
├── title: str (required)
├── description: str (optional)
├── severity: enum [critical, high, medium, low] (default: medium)
├── status: enum [detected, assessing, responding, contained, resolved, post_mortem] (default: detected)
├── category: enum [operational, security, legal, pr, supply_chain, hr, financial, other]
├── lead_id: UUID (FK → User/TeamMember, ondelete=SET NULL)
├── detected_at: datetime (required)
├── resolved_at: datetime (optional)
├── estimated_impact_usd: float (optional)
├── created_at: datetime
└── updated_at: datetime

TeamMember (Crisis Response Team)
├── id: UUID (PK)
├── name: str (required)
├── email: str (unique, required)
├── role: str (required)         -- e.g., "Incident Commander", "Legal Counsel", "Comms Lead"
├── department: str (optional)   -- e.g., "Legal", "Operations", "PR"
├── phone: str (optional)
├── is_active: bool (default true)
├── created_at: datetime
└── updated_at: datetime

ActionItem
├── id: UUID (PK)
├── crisis_id: UUID (FK → Crisis, ondelete=CASCADE)
├── title: str (required)
├── description: str (optional)
├── assignee_id: UUID (FK → TeamMember, ondelete=SET NULL)
├── status: enum [pending, in_progress, blocked, completed] (default: pending)
├── priority: enum [critical, high, medium, low] (default: medium)
├── due_at: datetime (optional)
├── completed_at: datetime (optional)
├── created_at: datetime
└── updated_at: datetime

Communication (Updates & Stakeholder Comms)
├── id: UUID (PK)
├── crisis_id: UUID (FK → Crisis, ondelete=CASCADE)
├── author_id: UUID (FK → TeamMember, ondelete=SET NULL)
├── message: str (required)
├── comm_type: enum [internal_update, stakeholder_alert, public_statement, exec_brief] (default: internal_update)
├── channel: enum [app, email, slack, sms] (default: app)
├── created_at: datetime
└── updated_at: datetime

Playbook (Crisis Response Templates)
├── id: UUID (PK)
├── name: str (required)
├── category: enum [operational, security, legal, pr, supply_chain, hr, financial, other]
├── description: str (optional)
├── steps: JSON (required)       -- ordered list of action templates
├── created_at: datetime
└── updated_at: datetime
```

### Key Relationships

- **Crisis** → has many **ActionItems**
- **Crisis** → has many **Communications**
- **Crisis** → has one **TeamMember** (lead)
- **ActionItem** → assigned to one **TeamMember**
- **Communication** → authored by one **TeamMember**
- **Crisis** → can link to a **Playbook** (optional, for auto-spawning action items)

---

## API Endpoints (v1.0)

```
GET    /api/v1/crisis              → List crises (with filters: status, severity, category)
POST   /api/v1/crisis              → Create crisis
GET    /api/v1/crisis/{id}         → Get crisis detail (with actions, comms)
PUT    /api/v1/crisis/{id}         → Update crisis
DELETE /api/v1/crisis/{id}         → Delete crisis
GET    /api/v1/crisis/{id}/timeline → Get chronological timeline

GET    /api/v1/team-members        → List team members
POST   /api/v1/team-members        → Create team member
GET    /api/v1/team-members/{id}   → Get team member
PUT    /api/v1/team-members/{id}   → Update team member
DELETE /api/v1/team-members/{id}   → Delete team member

GET    /api/v1/action-items        → List action items (filter by crisis, assignee, status)
POST   /api/v1/action-items        → Create action item
GET    /api/v1/action-items/{id}   → Get action item
PUT    /api/v1/action-items/{id}   → Update action item
DELETE /api/v1/action-items/{id}   → Delete action item

GET    /api/v1/communications      → List communications (filter by crisis, type)
POST   /api/v1/communications      → Post communication
GET    /api/v1/communications/{id} → Get communication
PUT    /api/v1/communications/{id} → Edit communication
DELETE /api/v1/communications/{id} → Delete communication

GET    /api/v1/playbooks           → List playbooks
POST   /api/v1/playbooks           → Create playbook
GET    /api/v1/playbooks/{id}      → Get playbook
PUT    /api/v1/playbooks/{id}      → Update playbook
DELETE /api/v1/playbooks/{id}      → Delete playbook

GET    /api/v1/dashboard           → Dashboard stats (active crises, open actions, avg resolution time, severity breakdown)
```

---

## Feature Roadmap (Complexity-Tiered)

### Complexity 0 — Core Foundational Elements (Quick Wins)

> These must be completed before any v1.0 feature work. They fix the broken scaffold state.

#### 0.1 Scaffold Alignment & Configuration
**Description:** Fix all misaligned ports, stale configs, and placeholder text across the codebase.
- **Backend:** Update `core/config.py` → `app_name="DClaw Crisis"`, `database_url` → `dclaw_crisis`
- **Backend:** Update `api/main.py` → title/version
- **Frontend:** Update `package.json` dev port → `3061`
- **Frontend:** Update `layout.tsx` → correct title/description
- **Infra:** Update `docker-compose.yml` → backend `8061`, frontend `3061`
- **Infra:** Update `AGENTS.md`/README port registry → add `dclaw-crisis` entry
- **Docs:** Rewrite `PRODUCT-SPEC.md` with Crisis domain model

#### 0.2 Core Database & Base Models
**Description:** Create all SQLAlchemy models with proper relationships, indexes, and enums.
- **Backend:** `app/models/crisis.py` — Crisis model
- **Backend:** `app/models/team_member.py` — TeamMember model
- **Backend:** `app/models/action_item.py` — ActionItem model
- **Backend:** `app/models/communication.py` — Communication model
- **Backend:** `app/models/playbook.py` — Playbook model
- **Backend:** `app/models/__init__.py` — import all models for Alembic
- **Infra:** Generate initial Alembic migration

#### 0.3 Pydantic Schemas
**Description:** Full request/response schemas for all entities with `ConfigDict(from_attributes=True)`.
- **Backend:** `app/schemas/crisis.py`
- **Backend:** `app/schemas/team_member.py`
- **Backend:** `app/schemas/action_item.py`
- **Backend:** `app/schemas/communication.py`
- **Backend:** `app/schemas/playbook.py`
- **Backend:** `app/schemas/__init__.py`

#### 0.4 Repositories
**Description:** Extend `BaseRepository` for each entity with domain-specific query methods.
- **Backend:** `app/repositories/crisis_repo.py` — `list_by_status`, `list_by_severity`, `get_with_actions`
- **Backend:** `app/repositories/team_member_repo.py`
- **Backend:** `app/repositories/action_item_repo.py` — `list_by_crisis`, `list_by_assignee`, `list_overdue`
- **Backend:** `app/repositories/communication_repo.py` — `list_by_crisis`
- **Backend:** `app/repositories/playbook_repo.py`
- **Backend:** `app/repositories/__init__.py`

#### 0.5 API Routers (Basic CRUD)
**Description:** Full CRUD endpoints for all 5 entities wired into `api/main.py`.
- **Backend:** `app/api/v1/crisis.py`
- **Backend:** `app/api/v1/team_members.py`
- **Backend:** `app/api/v1/action_items.py`
- **Backend:** `app/api/v1/communications.py`
- **Backend:** `app/api/v1/playbooks.py`
- **Backend:** `app/api/v1/__init__.py` + wire in `api/main.py`

#### 0.6 Backend Test Suite
**Description:** 70%+ coverage tests for all endpoints using `httpx.AsyncClient`.
- **Backend:** `tests/test_crisis.py`
- **Backend:** `tests/test_team_members.py`
- **Backend:** `tests/test_action_items.py`
- **Backend:** `tests/test_communications.py`
- **Backend:** `tests/test_playbooks.py`

#### 0.7 API Client (Frontend)
**Description:** Typed fetch wrapper functions for all backend endpoints.
- **Frontend:** Update `src/lib/api.ts` with all Crisis API functions

---

### Complexity 1 — Core Differentiators (Medium Complexity)

> These features make DClaw Crisis stand out from generic project management tools.

#### 1.1 Dashboard Page
**Description:** Operational command center showing real-time crisis metrics.
- **Frontend:** `src/app/page.tsx` — Summary cards (active crises, open action items, avg resolution time, critical count)
- **Frontend:** Severity breakdown bar chart
- **Frontend:** Recent communications feed
- **Frontend:** Quick-action buttons (declare crisis, add action item)
- **Backend:** `GET /api/v1/dashboard` aggregation endpoint
- **Backend:** Tests for dashboard endpoint

#### 1.2 Crisis List Page
**Description:** Table view of all crises with search, filter, and pagination.
- **Frontend:** `src/app/crisis/page.tsx` — Table with filtering by status, severity, category
- **Frontend:** Search by title/description
- **Frontend:** "Declare New Crisis" modal/form
- **Frontend:** Status badge coloring
- **Backend:** Already covered by 0.5 list endpoint with query params

#### 1.3 Crisis Detail Page
**Description:** Single crisis view with full context — info, action items, communications, timeline.
- **Frontend:** `src/app/crisis/[id]/page.tsx`
- **Frontend:** Crisis info card with severity/status editing
- **Frontend:** Action items list with inline status toggle
- **Frontend:** Communications timeline
- **Frontend:** Add action item / post update buttons
- **Backend:** `GET /api/v1/crisis/{id}/timeline` endpoint
- **Backend:** Tests for timeline endpoint

#### 1.4 Team Members Page
**Description:** Manage crisis response roster.
- **Frontend:** `src/app/team/page.tsx` — Table with role/department filters
- **Frontend:** Add/edit team member modal
- **Frontend:** Department badge display

#### 1.5 Action Items Kanban Board
**Description:** Trello-like board for action items grouped by status.
- **Frontend:** `src/app/action-items/page.tsx` — Kanban columns: Pending, In Progress, Blocked, Completed
- **Frontend:** Drag cards between columns (API update on drop)
- **Frontend:** Filter by crisis, assignee, priority

#### 1.6 Playbooks Page
**Description:** Create and manage crisis response templates.
- **Frontend:** `src/app/playbooks/page.tsx` — List view
- **Frontend:** Playbook detail with ordered step list
- **Frontend:** "Apply Playbook" button on crisis detail (auto-spawns action items)
- **Backend:** `POST /api/v1/crisis/{id}/apply-playbook/{playbook_id}` endpoint
- **Backend:** Tests for apply-playbook endpoint

---

### Complexity 2 — Advanced Features (High Complexity / AI Integrations)

> These are the features that make investors say "this is the future of crisis management."

#### 2.1 AI Crisis Summarizer
**Description:** Auto-generate an executive summary of any crisis from all communications, action items, and status changes.
- **Backend:** `app/services/ai_summarizer.py` — GPT-based summarization
- **Backend:** `POST /api/v1/crisis/{id}/summarize` endpoint
- **Frontend:** "Generate Summary" button on crisis detail → renders AI executive brief
- **Backend:** Tests with mocked LLM calls

#### 2.2 AI Next-Best-Action Recommender
**Description:** Based on crisis category, stage, missing action items, and elapsed time, recommend the next action item a team should take.
- **Backend:** `app/services/ai_recommender.py` — Rule-based + LLM hybrid engine
- **Backend:** `GET /api/v1/crisis/{id}/next-action` endpoint
- **Frontend:** "AI Suggestion" card on crisis detail with one-click accept
- **Backend:** Tests

#### 2.3 AI Communication Draft Generator
**Description:** Auto-draft stakeholder alerts and public statements from crisis context.
- **Backend:** `app/services/ai_comm_draft.py` — Generate draft comms from crisis data
- **Backend:** `POST /api/v1/communications/draft` endpoint
- **Frontend:** "AI Draft" option when posting communication

#### 2.4 Crisis Severity Auto-Escalation Engine
**Description:** If action items are overdue, communications are stale, or manual severity upgrade is pending, auto-escalate severity and notify lead.
- **Backend:** Background task (APScheduler or Celery): `app/services/escalation_engine.py`
- **Backend:** `POST /api/v1/crisis/{id}/escalate` endpoint
- **Frontend:** Visual escalation indicators (flashing severity badge)

#### 2.5 Real-Time Timeline & Audit Log
**Description:** Immutable, append-only timeline of every change to a crisis. Full compliance-grade audit trail.
- **Backend:** `app/models/audit_log.py` — Auto-generated on every update via event listener
- **Backend:** `GET /api/v1/crisis/{id}/audit-log` endpoint
- **Frontend:** Timeline view with color-coded event types (status change, action completed, comm posted)

#### 2.6 Analytics & Reporting
**Description:** Organization-level crisis analytics for post-mortems and trend analysis.
- **Backend:** `GET /api/v1/analytics/overview` — MTTR, crisis frequency by category, team performance
- **Backend:** `GET /api/v1/analytics/team/{member_id}` — Individual response metrics
- **Frontend:** `src/app/analytics/page.tsx` — Charts (recharts or chart.js)
- **Frontend:** Export to PDF/CSV

#### 2.7 Notification System (WebSocket / SSE)
**Description:** Real-time push notifications when crises are updated, action items assigned, or escalations occur.
- **Backend:** FastAPI WebSocket endpoint `/ws/crisis/{id}`
- **Frontend:** WebSocket hook for live updates on crisis detail + dashboard
- **Frontend:** Toast notifications for new assignments and escalations

---

## Implementation Priority Order

| Phase | Features | Complexity | Est. Effort |
|-------|----------|------------|-------------|
| **Phase 0: Foundation** | 0.1–0.7 | 0 | 2–3 sessions |
| **Phase 1: Core App** | 1.1–1.6 | 0–1 | 3–4 sessions |
| **Phase 2: AI Copilot** | 2.1–2.3 | 2 | 2 sessions |
| **Phase 3: Intelligence** | 2.4–2.7 | 2 | 3–4 sessions |

---

## Non-Functional Requirements

- **Backend tests:** 70%+ coverage, all async tests with `pytest_asyncio==0.24.0`
- **Frontend:** Responsive layout, Tailwind + pre-built UI components only
- **Database:** PostgreSQL, all timestamps naive UTC via `utc_now()`
- **Docker:** `docker compose up -d` starts all services with healthy status
- **Alembic:** Every schema change gets a migration
- **Code quality:** No hardcoded ports/URLs, no mock data, repository pattern enforced

---

## Updated Frontmatter

| Property | Value |
|----------|-------|
| App Name | DClaw Crisis |
| Domain | Crisis & Incident Management |
| Target User | Operations, Legal, PR, HR, Security teams |
| Backend Port | 8061 |
| Frontend Port | 3061 |
| Database | dclaw_crisis |
| Base API Path | /api/v1 |
| YC Thesis | AI-native Crisis Command Center for non-technical teams |
