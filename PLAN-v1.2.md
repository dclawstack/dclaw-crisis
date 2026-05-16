# CRM — v1.2 Feature Roadmap

> 📘 **REVISED PRD v2.3 available:** See `REVISED-PRD.md` for complete gap analysis, current state, and full feature roadmap.


> **For coding agents:** Pick features from this list, implement them fully, and update this doc with a checkmark.
> **Do NOT change the basic stack.** See `AGENTS.md` for architecture lock.

## Pre-Flight Checklist — Do This First

Before implementing any v1.2 feature, verify:

- [x] `frontend/package-lock.json` is committed after any `npm install` / dependency change
- [x] `frontend/next-env.d.ts` exists and is committed (required for Next.js TypeScript builds)
- [x] `frontend/.gitignore` excludes `node_modules/` and `.next/`
- [x] `docker-compose.yml` healthchecks use `python urllib.request.urlopen()` (backend) and `wget -q --spider` (frontend)
- [x] `frontend/Dockerfile` declares `ARG NEXT_PUBLIC_API_URL` before `RUN npm run build`

## v1.0 Feature Inventory (Current)

- [x] Core entity CRUD: Crisis, TeamMember, ActionItem, Communication, Playbook
- [x] Dashboard / main page
- [x] Real backend CRUD (no mocks)
- [x] Docker + Helm deployment
- [x] Alembic migrations
- [x] Backend tests (22 tests, 100% pass)

---

## v1.2 Roadmap

### P0 — Must Have (Complexity 0)

#### 0.1 Scaffold Alignment & Configuration
**Description:** Fix all misaligned ports, stale configs, and placeholder text across the codebase.
- [x] Backend: `core/config.py` → `app_name="DClaw Crisis"`, `database_url` → `dclaw_crisis`
- [x] Backend: `api/main.py` → title/version, wire v1 routers
- [x] Frontend: `package.json` dev port → `3061`
- [x] Frontend: `layout.tsx` → correct title/description
- [x] Infra: `docker-compose.yml` → backend `8061`, frontend `3061`, postgres `5437:5432`
- [x] Infra: `AGENTS.md`/README port registry → `dclaw-crisis` entry
- [x] Docs: Rewrite `PRODUCT-SPEC.md` with Crisis domain model

#### 0.2 Core Database & Base Models
**Description:** Create all SQLAlchemy models with proper relationships, indexes, and enums.
- [x] `app/models/crisis.py` — Crisis model with severity, status, category enums
- [x] `app/models/team_member.py` — TeamMember model
- [x] `app/models/action_item.py` — ActionItem model with status, priority enums
- [x] `app/models/communication.py` — Communication model with comm_type, channel enums
- [x] `app/models/playbook.py` — Playbook model with JSON steps
- [x] `app/models/__init__.py` — import all models for Alembic
- [x] Infra: Generate initial Alembic migration (`708d965e76ca_initial_crisis_models`)

#### 0.3 Pydantic Schemas
**Description:** Full request/response schemas for all entities with `ConfigDict(from_attributes=True)`.
- [x] `app/schemas/crisis.py` — CrisisCreate, CrisisUpdate, CrisisResponse
- [x] `app/schemas/team_member.py` — TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
- [x] `app/schemas/action_item.py` — ActionItemCreate, ActionItemUpdate, ActionItemResponse
- [x] `app/schemas/communication.py` — CommunicationCreate, CommunicationUpdate, CommunicationResponse
- [x] `app/schemas/playbook.py` — PlaybookCreate, PlaybookUpdate, PlaybookResponse, PlaybookStep

#### 0.4 Repositories
**Description:** Extend `BaseRepository` for each entity with domain-specific query methods.
- [x] `app/repositories/crisis_repo.py` — `list_by_status`, `list_by_severity`, `list_by_category`
- [x] `app/repositories/team_member_repo.py`
- [x] `app/repositories/action_item_repo.py` — `list_by_crisis`, `list_by_assignee`, `list_overdue`
- [x] `app/repositories/communication_repo.py` — `list_by_crisis`
- [x] `app/repositories/playbook_repo.py`

#### 0.5 API Routers (Basic CRUD)
**Description:** Full CRUD endpoints for all 5 entities + dashboard, wired into `api/main.py`.
- [x] `app/api/v1/crisis.py` — `/api/v1/crisis/`
- [x] `app/api/v1/team_members.py` — `/api/v1/team-members/`
- [x] `app/api/v1/action_items.py` — `/api/v1/action-items/`
- [x] `app/api/v1/communications.py` — `/api/v1/communications/`
- [x] `app/api/v1/playbooks.py` — `/api/v1/playbooks/`
- [x] `app/api/v1/dashboard.py` — `/api/v1/dashboard/`

#### 0.6 Backend Test Suite
**Description:** 22 tests for all endpoints using `httpx.AsyncClient`.
- [x] `tests/test_crisis.py`
- [x] `tests/test_team_members.py`
- [x] `tests/test_action_items.py`
- [x] `tests/test_communications.py`
- [x] `tests/test_playbooks.py`
- [x] `tests/test_dashboard.py`

#### 0.7 API Client (Frontend)
**Description:** Typed fetch wrapper functions for all backend endpoints.
- [x] `src/lib/api.ts` — Dashboard, Crisis, TeamMember, ActionItem, Communication, Playbook APIs

---

### P1 — Should Have (Complexity 1)

#### 1.1 Dashboard Page
**Description:** Operational command center showing real-time crisis metrics.
- [x] `src/app/page.tsx` — Summary cards, severity/status breakdown, recent lists
- [x] Backend: `GET /api/v1/dashboard` aggregation endpoint

#### 1.2 Crisis List Page
**Description:** Table view of all crises with search, filter, and pagination.
- [x] `src/app/crisis/page.tsx` — Table with filtering by status, severity, category
- [x] Search by title/description
- [x] "Declare New Crisis" modal/form
- [x] Status badge coloring

#### 1.3 Crisis Detail Page
**Description:** Single crisis view with full context — info, action items, communications.
- [x] `src/app/crisis/[id]/page.tsx`
- [x] Crisis info card with severity/status editing
- [x] Action items list with inline status toggle
- [x] Communications timeline
- [x] Add action item / post update buttons

#### 1.4 Team Members Page
**Description:** Manage crisis response roster.
- [x] `src/app/team/page.tsx` — Table with role/department filters
- [x] Add/edit team member modal
- [x] Department badge display

#### 1.5 Action Items Board
**Description:** Kanban-like board for action items grouped by status.
- [x] `src/app/action-items/page.tsx` — Columns: Pending, In Progress, Blocked, Completed
- [x] Move cards between columns
- [x] Filter by status

#### 1.6 Playbooks Page
**Description:** Create and manage crisis response templates.
- [x] `src/app/playbooks/page.tsx` — List view with steps
- [x] Create/edit playbook modal with dynamic steps

---

### P2 — Could Have (Complexity 2)

#### 2.1 AI Crisis Summarizer
**Description:** Auto-generate an executive summary of any crisis.
- [ ] `app/services/ai_summarizer.py`
- [ ] `POST /api/v1/crisis/{id}/summarize`

#### 2.2 AI Next-Best-Action Recommender
**Description:** Recommend the next action item a team should take.
- [ ] `app/services/ai_recommender.py`
- [ ] `GET /api/v1/crisis/{id}/next-action`

#### 2.3 AI Communication Draft Generator
**Description:** Auto-draft stakeholder alerts from crisis context.
- [ ] `app/services/ai_comm_draft.py`
- [ ] `POST /api/v1/communications/draft`

#### 2.4 Crisis Severity Auto-Escalation Engine
**Description:** Auto-escalate if action items are overdue.
- [ ] `app/services/escalation_engine.py`

#### 2.5 Real-Time Timeline & Audit Log
**Description:** Immutable timeline of every change to a crisis.
- [ ] `app/models/audit_log.py`

#### 2.6 Analytics & Reporting
**Description:** Organization-level crisis analytics.
- [ ] `GET /api/v1/analytics/overview`
- [ ] `src/app/analytics/page.tsx`

#### 2.7 Notification System (WebSocket / SSE)
**Description:** Real-time push notifications.
- [ ] FastAPI WebSocket endpoint `/ws/crisis/{id}`
- [ ] Toast notifications for new assignments and escalations

---

## Implementation Priority

1. ~~P0: Foundation~~ ✅ Completed
2. ~~P1: Core Differentiators~~ ✅ Completed
3. P2: Advanced AI & Real-time features → Next sprint
