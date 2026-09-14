# Roadmap: PantryTrack — Household Food Inventory PoC (Group 2 Monday)

## Overview

This roadmap delivers the PantryTrack PoC by completing the existing Flask/MongoDB/React scaffold
(routes and DB modules are stubbed but not implemented; client pages/components are still named
generically after the assignment's "project"/"hardware set" template). Work is organized into
**three parallel tracks**, one per developer, following the codebase's existing module seams
rather than a sequential build order:

- **Track A / Phase 1 — Account & Household Management**: everything in `usersDatabase.py` plus
  the household-CRUD/membership half of `projectsDatabase.py` (households replace "projects"),
  and the `MyLoginPage` / `MyRegistrationPage` / household-list parts of the frontend.
- **Track B / Phase 2 — Inventory Management**: everything in `hardwareDatabase.py` (food item
  stock replaces "hardware sets") plus the reserve/consume/restock half of `projectsDatabase.py`,
  and the `Checkout` / capacity-availability-by-location parts of the frontend.
- **Track C / Phase 3 — Data Integration, API & Cloud Deployment**: cross-cutting work that only
  fully resolves once Tracks A and B have landed — eliminating hard-coded data everywhere,
  hardening the REST API layer, writing PyTest coverage, and deploying to a public URL. Track C's
  *infrastructure* sub-tasks (Mongo Atlas provisioning, deployment pipeline skeleton, PyTest
  harness scaffolding) can start on day one in parallel with Tracks A and B; only the final
  integration/verification/deploy sub-tasks are gated on A and B substantially landing.

**Explicit coordination point:** Phase 1 and Phase 2 both edit `server/projectsDatabase.py` (the
household document). Phase 1 owns household CRUD and membership (create household, join
household, look up a user's households). Phase 2 owns item-quantity updates (reserve, consume/
checkout, restock/check-in). Agree on the household document's item-stock shape (capacity/
availability per item, keyed by location — Pantry/Fridge/Freezer) before both tracks start writing
to it, to avoid merge conflicts and schema drift.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Account & Household Management** - Users can securely register, log in, stay signed in, and create or join a household
- [ ] **Phase 2: Inventory Management** - Users can view pantry/fridge/freezer inventory by location, reserve items, consume/checkout items, restock/check-in items, and see freshness flags
- [ ] **Phase 3: Data Integration, API & Cloud Deployment** - The app runs entirely on live MongoDB/REST data, is test-covered, and is reachable via a public URL

## Phase Details

### Phase 1: Account & Household Management
**Goal**: A household member can securely create an account, log in, stay logged in, and create or join a household to track shared food inventory within.
**Depends on**: Nothing (first phase — can start immediately in parallel with Phase 2 and Phase 3's infra sub-tasks)
**Requirements**: ACCT-01, ACCT-02, ACCT-03, ACCT-04, HH-01, HH-02, HH-03
**Success Criteria** (what must be TRUE):
  1. A new user can register via the "New User" sign-up form and immediately log in with those same credentials.
  2. Userid and password are never stored or transmitted in plaintext (encrypted at rest and in transit).
  3. A logged-in user remains logged in while navigating between pages within the app (session persists).
  4. A user can create a new household by supplying a name, description, and householdID.
  5. A user can join an existing household by entering its householdID, and can see the list of every household they belong to.
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 01-01: TBD

### Phase 2: Inventory Management
**Goal**: Within a household, a member can see what food is on hand across pantry/fridge/freezer and reserve, consume, or restock items without ever over-committing what's available.
**Depends on**: Phase 1 (shares the household document / `projectsDatabase.py` — coordinate on the item-stock schema early). Development can proceed in parallel using seeded/test household data; the hard dependency is only at cross-track integration testing.
**Requirements**: INV-01, INV-02, INV-03, INV-04, INV-05
**Success Criteria** (what must be TRUE):
  1. A user can view all food items in a household's inventory grouped by location (Pantry / Fridge / Freezer), each showing capacity (total units stocked) and availability (units not yet reserved or consumed).
  2. A user can restock an item — adding a quantity along with a purchase date and a best-by/expiration date ("check-in").
  3. A user can reserve/claim a quantity of an item for themselves without removing it from the shared inventory ("request").
  4. A user can consume/remove a quantity of an item from inventory ("checkout"), and the action is rejected if it would exceed what's currently available.
  5. Every item displays a freshness flag (fresh / expiring soon / expired) computed from its best-by date compared to today — no sensor or ML input required.
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 02-01: TBD

### Phase 3: Data Integration, API & Cloud Deployment
**Goal**: The full application runs against a live MongoDB-backed REST API with zero hard-coded data anywhere, is covered by automated tests, and is deployed to a cloud host reachable by the instructor/TAs.
**Depends on**: Phase 1 and Phase 2 for final integration, verification, and deploy (needs both feature sets substantially implemented to confirm no hard-coded data remains, exercise the full REST surface, and write meaningful route tests). Infra sub-tasks (MongoDB Atlas provisioning, deployment config skeleton, PyTest harness scaffolding, API response conventions) can start on day one in parallel with Phase 1 and Phase 2.
**Requirements**: DATA-01, DATA-02, DATA-03, OPS-01, OPS-02
**Success Criteria** (what must be TRUE):
  1. All user, household, and food-item data lives in MongoDB collections, and every CRUD operation for each goes through a REST endpoint (no other data path exists).
  2. Every page in the app (login, household portal/list, inventory view, reserve/consume/restock) renders its data — capacity, availability, household list, item details, freshness flags — from a live REST API call, with no hard-coded or mock values remaining in any component.
  3. Automated PyTest tests exist and pass for the core backend routes: login, create household, join household, reserve, consume, restock.
  4. The deployed app is reachable at a public URL, and the instructor/TAs can complete the full account → household → reserve/consume/restock flow against the hosted instance.
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 03-01: TBD

## Progress

**Execution Order:**
Phase 1 and Phase 2 execute in parallel (independent tracks, one coordination point on `projectsDatabase.py`'s household document). Phase 3's infra sub-tasks start alongside them; Phase 3's integration/verification/deploy sub-tasks complete last, after Phase 1 and Phase 2 land.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Account & Household Management | 0/TBD | Not started | - |
| 2. Inventory Management | 0/TBD | Not started | - |
| 3. Data Integration, API & Cloud Deployment | 0/TBD | Not started | - |

---
*Roadmap created: 2026-09-14*
*Granularity: standard | Phase ID convention: sequential*
