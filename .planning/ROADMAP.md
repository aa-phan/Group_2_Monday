# Roadmap: PantryTrack — Household Food Inventory PoC (Group 2 Monday)

## Overview

This roadmap delivers the PantryTrack PoC by completing the existing Flask/MongoDB/React scaffold
(routes and DB modules are stubbed but not implemented; client pages/components are still named
generically after the assignment's "project"/"hardware set" template). Work is organized into
**four parallel tracks**, one per developer (the team confirmed 4 developers), following the
codebase's existing module seams rather than a sequential build order:

- **Track A — Account & Household Management**: everything in `usersDatabase.py` plus
  the household-CRUD/membership half of `projectsDatabase.py` (households replace "projects"),
  and the `MyLoginPage` / `MyRegistrationPage` / household-list parts of the frontend.
- **Track B — Inventory Management**: everything in `hardwareDatabase.py` (food item
  stock replaces "hardware sets") plus the reserve/consume/restock half of `projectsDatabase.py`,
  and the `Checkout` / capacity-availability-by-location parts of the frontend.
- **Track C — Data Integration & API**: eliminating hard-coded data everywhere and
  hardening the REST API layer so it only fully resolves once Tracks A and B have landed. Track
  C's *infrastructure* sub-tasks (Mongo Atlas provisioning, API response conventions) can start on
  day one in parallel with Tracks A and B; only the final integration/verification sub-tasks are
  gated on A and B substantially landing. Track C also owns two promoted stretch features
  (password reset, custom storage locations) as its own committed Phase 2 scope, since only 3 of
  the 4 tracks can own one of the 3 real Phase 2 rubric items.
- **Track D — Deployment & Quality**: writing PyTest coverage for the core backend routes and
  deploying the app to a public cloud URL. Track D's *infrastructure* sub-tasks (deployment
  pipeline skeleton, PyTest harness scaffolding) can start on day one in parallel with the other
  tracks; only the final integration/verification/deploy sub-tasks are gated on Tracks A, B, and C
  substantially landing.

**Explicit coordination point:** Track A and Track B both edit `server/projectsDatabase.py` (the
household document). Track A owns household CRUD and membership (create household, join
household, look up a user's households). Track B owns item-quantity updates (reserve, consume/
checkout, restock/check-in). Agree on the household document's item-stock shape (capacity/
availability per item, keyed by location — Pantry/Fridge/Freezer) before both tracks start writing
to it, to avoid merge conflicts and schema drift.

## Phases

**Track Ordering:** Tracks A, B, C, and D run in parallel (one per developer, split along existing
module seams) rather than a strict numeric sequence — see the coordination point above and each
track's "Depends on" line for the one place they touch.

> **Note on "Phase N" below:** The `Phase N` numbers in this section's headings are GSD's own
> internal phase-tracking IDs (required by the planning tooling to parse this file) — they are
> **not** the assignment's Phase 1/Phase 2 grading milestones, and they don't align with them
> 1:1 (e.g. GSD's "Phase 2" is Track B, whose own rubric ownership spans both the assignment's
> Phase 1 *and* Phase 2 — see each track's Rubric ownership line in `WORK-ITEMS.md`). Treat
> **Track A/B/C/D** as the real work-breakdown label everywhere in this project; the `Phase N`
> prefix here exists solely so `/gsd-discuss-phase`, `/gsd-plan-phase`, etc. can locate each
> track's section.

- [ ] **Phase 1 (Track A): Account & Household Management** - Users can securely register, log in, stay signed in, and create or join a household
- [ ] **Phase 2 (Track B): Inventory Management** - Users can view pantry/fridge/freezer inventory by location, reserve items, consume/checkout items, restock/check-in items, and see freshness flags
- [ ] **Phase 3 (Track C): Data Integration & API** - The app runs entirely on live MongoDB/REST data, and Track C's own promoted stretch features (password reset, custom storage locations) are delivered
- [ ] **Phase 4 (Track D): Deployment & Quality** - The app is test-covered and reachable via a public URL

## Phase Details

### Phase 1 (Track A): Account & Household Management

**Goal**: A household member can securely create an account, log in, stay logged in, and create or join a household to track shared food inventory within.
**Depends on**: Nothing (first track — can start immediately in parallel with Track B and Track C's infra sub-tasks)
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

### Phase 2 (Track B): Inventory Management

**Goal**: Within a household, a member can see what food is on hand across pantry/fridge/freezer and reserve, consume, or restock items without ever over-committing what's available.
**Depends on**: Track A (shares the household document / `projectsDatabase.py` — coordinate on the item-stock schema early). Development can proceed in parallel using seeded/test household data; the hard dependency is only at cross-track integration testing.
**Requirements**: INV-01, INV-02, INV-03, INV-04, INV-05
**Success Criteria** (what must be TRUE):

  1. A user can view all food items in a household's inventory grouped by location (Pantry / Fridge / Freezer), each showing capacity (total units stocked) and availability (units not yet reserved or consumed).
  2. A user can restock an item — adding a quantity along with a purchase date and a best-by/expiration date ("check-in").
  3. A user can reserve/claim a quantity of an item for themselves without removing it from the shared inventory ("request").
  4. A user can consume/remove a quantity of an item from inventory ("checkout"), and the action is rejected if it would exceed what's currently available.
  5. Every item displays a freshness flag (fresh / expiring soon / expired) computed from its best-by date compared to today — no sensor or ML input required.

**Plans**: 4 plans
**UI hint**: yes

Plans:
**Wave 1**

- [ ] 02-01-PLAN.md — Tracer: restock one item into a location and see it in the inventory view (INV-01, INV-02)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 02-02-PLAN.md — Location-specific freshness flags: Pantry, Fridge, and Freezer rule-sets (INV-05)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 02-03-PLAN.md — Item identity matching across restocks and per-item batch detail (INV-01, INV-02)

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 02-04-PLAN.md — Reserve, release, and FIFO consume with the overbooking guard (INV-03, INV-04)

### Phase 3 (Track C): Data Integration & API

**Goal**: The full application runs against a live MongoDB-backed REST API with zero hard-coded data anywhere, and Track C's own promoted stretch features (password reset, custom storage locations) are delivered as its Phase 2 scope.
**Depends on**: Track A and Track B for final integration and verification (needs both feature sets substantially implemented to confirm no hard-coded data remains and exercise the full REST surface). Infra sub-tasks (MongoDB Atlas provisioning, API response conventions) can start on day one in parallel with Track A and Track B.
**Requirements**: DATA-01, DATA-02, DATA-03, STRETCH-01, STRETCH-02
**Success Criteria** (what must be TRUE):

  1. All user, household, and food-item data lives in MongoDB collections, and every CRUD operation for each goes through a REST endpoint (no other data path exists).
  2. Every page in the app (login, household portal/list, inventory view, reserve/consume/restock) renders its data — capacity, availability, household list, item details, freshness flags — from a live REST API call, with no hard-coded or mock values remaining in any component.
  3. A user who forgot their password can reset it via the existing Forgot Password flow and regain access to their household's inventory.
  4. A household member can define storage locations beyond the default Pantry/Fridge/Freezer (e.g. a garage freezer or wine fridge).

**Plans**: TBD
**UI hint**: yes

Plans:

- [ ] 03-01: TBD

### Phase 4 (Track D): Deployment & Quality

**Goal**: The PoC is reachable by the instructor/TAs via a public URL and its core flows are covered by automated tests.
**Depends on**: Track A, Track B, and Track C for final integration, verification, and deploy (needs the feature sets substantially implemented to write meaningful route tests and confirm the deployed app is fully functional). Infra sub-tasks (deployment config skeleton, PyTest harness scaffolding) can start on day one in parallel with the other tracks.
**Requirements**: OPS-01, OPS-02
**Success Criteria** (what must be TRUE):

  1. Automated PyTest tests exist and pass for the core backend routes: login, create household, join household, reserve, consume, restock.
  2. The deployed app is reachable at a public URL, and the instructor/TAs can complete the full account → household → reserve/consume/restock flow against the hosted instance.

**Plans**: TBD
**UI hint**: no

Plans:

- [ ] 04-01: TBD

## Progress

**Execution Order:**
Track A and Track B execute in parallel (independent tracks, one coordination point on `projectsDatabase.py`'s household document). Track C's and Track D's infra sub-tasks start alongside them; Track C's integration/verification sub-tasks and Track D's integration/verification/deploy sub-tasks complete last, after Track A, Track B, and (for Track D) Track C substantially land.

| Track | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| A. Account & Household Management | 0/TBD | Not started | - |
| B. Inventory Management | 0/4 | Planned | - |
| C. Data Integration & API | 0/TBD | Not started | - |
| D. Deployment & Quality | 0/TBD | Not started | - |

---
*Roadmap created: 2026-09-14*
*Last updated: 2026-09-14 after restructuring to 4-track parallel structure (4 developers)*
*Granularity: standard | Phase ID convention: sequential*
