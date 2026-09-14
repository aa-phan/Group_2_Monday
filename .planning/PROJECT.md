# HaaS PoC (Group 2 Monday — MIS385N Team Project)

## What This Is

A Proof-of-Concept web application for a Hardware-as-a-Service (HaaS) system, inspired by the University of Utah POWDER program. Users create secure accounts, create or join projects, and use those projects to view, request, checkout, and check-in shared hardware resources (HWSet1, HWSet2, ...). Built with a Flask/MongoDB backend and a React frontend (starter scaffold already exists in `server/` and `client/`).

## Core Value

A user can securely log in, join or create a project, and check hardware resources out of and back into a live, database-backed inventory — with no hard-coded data anywhere in the app.

## Business Context

- **Customer**: Course instructor (Dr. Samant) and TAs, grading against the Team Project rubric (MIS385N, Fa26)
- **Revenue model**: N/A — academic PoC, not monetized
- **Success metric**: Phase 1 (5 pts) and Phase 2 (10 pts) rubric criteria fully met; app hosted and reachable via URL by end of Phase 2
- **Strategy notes**: See `Team Project_Fa26.pdf` in repo root for the full assignment spec

## Requirements

### Validated

- ✓ Starter scaffold exists — Flask backend (`app.py`, `usersDatabase.py`, `projectsDatabase.py`, `hardwareDatabase.py`) and React frontend (`MyLoginPage`, `MyRegistrationPage`, `MyUserPortal`, `ForgotMyPassword`, `Project`, `Checkout` components) — pre-existing
- ✓ Backend route surface already sketched: `/login`, `/main`, `/join_project`, `/add_user`, `/get_user_projects_list`, `/create_project`, `/get_project_info`, `/get_all_hw_names`, `/get_hw_info`, `/check_out`, `/check_in`, `/create_hardware_set`, `/api/inventory` — pre-existing

### Active

- [ ] Secure sign-in / new-user creation (SN1)
- [ ] Userid/password encryption (SN1, SR3)
- [ ] Create new project (name, description, projectID) (SN1, SR4)
- [ ] Join / access existing project by projectID (SN1, SR4)
- [ ] View capacity + availability of HWSet1/HWSet2 (SN2)
- [ ] Request available hardware resources (SN3)
- [ ] Checkout hardware resources into a project (SN4)
- [ ] Check-in hardware resources back to inventory (SN5)
- [ ] Persist users, projects, and hardware in MongoDB — no hard-coded data on any page (SR5, R2-2)
- [ ] REST API layer for all DB access (SR2, R2-1)
- [ ] Cloud hosting reachable via URL for TAs/instructor (R2-3)
- [ ] Project board with all features + initial work items (user stories, tech debt, research items) (R1-2)
- [ ] High-level architecture sketch (R1-3)

### Out of Scope

- OAuth / third-party login — assignment scope is username/password only; SN1 only requires "secure user accounts", course stack doesn't call for it
- Real-time multi-user collaboration on a project — not a stated stakeholder need, adds complexity beyond PoC
- Mobile app — web-only PoC per SR2
- Billing/payment (despite HaaS/XaaS framing) — out of scope per assignment; PoC only needs account + resource lifecycle, not commerce

## Context

- This is a graded academic team project (MIS385N Advanced Programming & App Development), delivered in phases with a shared grading rubric (`Team Project_Fa26.pdf`).
- Phase 1 (5 pts, due first) requires: a Project Plan (team, sprint velocity, tools, methodology), all features + initial work items on a board, a high-level sketch of the app, and a stated tool/approach choice. No code delivery required yet.
- Phase 2 (10 pts) requires all General Requirements satisfied: hardware resources stored in DB with an API, user/project info accessible from the app with no hard-coded data, and the app hosted on the cloud and reachable via URL.
- General requirements apply across all phases: single shared repo (instructor + TAs added as collaborators), issue tracker kept separate from the user-story board, all user stories defined by end of Phase 1 (refined later), each user story describable in ≤3 sentences.
- Recommended/expected stack per assignment: Python (Flask), React.js, MongoDB, PyTest, Heroku Cloud Deploy — matches the existing scaffold, so no stack discussion needed with the TA.
- Existing scaffold is a bare-bones starter template (routes stubbed, DB helper modules stubbed) — not yet wired to a real MongoDB instance, no encryption implemented, no tests, no deployment config.

## Constraints

- **Tech stack**: Flask + MongoDB + React (+ PyTest, Heroku) — per course-recommended stack; the existing scaffold already assumes this, and deviating requires a TA discussion
- **Timeline**: Phase 1 and Phase 2 have hard course-calendar due dates (exact dates not yet provided by user — confirm against syllabus/Canvas)
- **Team size**: 5–6 students max, single shared GitHub repo for all phases, instructor + TAs must have repo access
- **Process**: User stories must be ≤3 sentences (Mountain Goat Software style); issues (bugs/improvements) tracked separately from user-story board, not combined
- **Security**: Userid and password must be encrypted at rest/in transit (SR3) — non-negotiable rubric item

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build on existing `server/`/`client/` scaffold rather than starting fresh | Scaffold already encodes the assignment's expected route surface and DB module boundaries | — Pending |
| Skip formal research phase (stack/features/architecture) | Assignment PDF fully specifies stakeholder needs, requirements, and recommended stack — external research adds no value here | ✓ Good |
| Skip codebase-mapping subagent | Existing scaffold is small (4 backend files, handful of React pages); read directly instead of spawning a mapper | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-14 after initialization*
