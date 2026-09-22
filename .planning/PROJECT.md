# PantryTrack — Household Food Inventory PoC (Group 2 Monday — MIS385N Team Project)

## What This Is

A Proof-of-Concept web application that lets members of a household track shared food inventory across the pantry, fridge, and freezer. Users create secure accounts, create or join a household, and use it to see what food is on hand, reserve items for themselves, log consumption, and log restocking — all backed by a live database, with the class's HaaS "hardware resource" concept reframed as **food item stock** (each item has a total capacity and a remaining availability, the same shape as the assignment's HWSet1/HWSet2 mockup). Built with a Flask/MongoDB backend and a React frontend (starter scaffold already exists in `server/` and `client/`).

## Core Value

A household member can see what food the household has across pantry/fridge/freezer, reserve or consume items, and restock — all from live shared data, with no hard-coded values anywhere in the app.

## Business Context

- **Customer**: Course instructor (Dr. Samant) and TAs, grading against the Team Project rubric (MIS385N, Fa26)
- **Revenue model**: N/A — academic PoC, not monetized
- **Success metric**: Phase 1 (5 pts) and Phase 2 (10 pts) rubric criteria fully met; app hosted and reachable via URL by end of Phase 2
- **Strategy notes**: See `Team Project_Fa26.pdf` in repo root for the full assignment spec. POWDER (cited in the PDF) is inspiration for the general HaaS shape only — nothing wireless/RF-specific applies here.
- **Team structure**: The team now has 4 developers on 4 tracks (Track A: Account & Household Management, Track B: Inventory Management, Track C: Data Integration & API, Track D: Deployment & Quality). Each track owns exactly one Phase 1 rubric item and one Phase 2 rubric item, except Track C, whose Phase 2 scope is a promoted stretch-feature set (STRETCH-01, STRETCH-02) instead of a numbered R2 item.

## Requirements

### Validated

- ✓ Starter scaffold exists — Flask backend (`app.py`, `usersDatabase.py`, `projectsDatabase.py`, `hardwareDatabase.py`) and React frontend (`MyLoginPage`, `MyRegistrationPage`, `MyUserPortal`, `ForgotMyPassword`, `Project`, `Checkout` components) — pre-existing, to be repurposed: `projectsDatabase.py` → households, `hardwareDatabase.py` → food item stock
- ✓ Backend route surface already sketched: `/login`, `/main`, `/join_project`, `/add_user`, `/get_user_projects_list`, `/create_project`, `/get_project_info`, `/get_all_hw_names`, `/get_hw_info`, `/check_out`, `/check_in`, `/create_hardware_set`, `/api/inventory` — pre-existing, semantics reframed (see below)
- ✓ View food inventory by location with capacity/availability (SN2) — Track B, Phase 2 (Track B), 4/4 plans, UAT passed
- ✓ Reserve/claim a quantity of an item for oneself (SN3) — Track B, unenforced "dibs" flag, not a hold
- ✓ Consume/remove a quantity of an item from inventory ("checkout") (SN4) — Track B, FIFO by best-by date, overbooking guard with optimistic concurrency (independently race-tested against a real MongoDB, not mongomock)
- ✓ Restock / add new item quantity to inventory ("check-in") (SN5) — Track B, batch-per-restock model with substring/prefix item-name matching
- ✓ Simple date-based freshness flag (SN2 extension) — Track B, three genuinely different rule-sets per location (Pantry: none, Fridge: 3-day window, Freezer: purchase-date-driven quality band, not a safety signal)
- ✓ Persist food items in MongoDB, no hard-coded data (SR5, R2-2 half) — Track B's half; user/household half remains Track A's responsibility
- ✓ REST API layer for inventory operations (SR2, R2-1 half) — Track B's half (`/api/inventory`, `/restock`, `/consume`, `/reserve`, `/release`)

### Active

**MVP (must satisfy SN1–SN6):**

- [ ] Secure sign-in / new-user creation (SN1)
- [ ] Userid/password encryption (SN1, SR3)
- [ ] Create new household (name, description, householdID) (SN1, SR4)
- [ ] Join / access existing household by householdID (SN1, SR4)
- [ ] Persist users and household membership in MongoDB — no hard-coded data on any page (SR5, R2-2 remainder — Track A's half; Track B's food-item half is validated above)
- [ ] REST API layer for user/household operations (SR2, R2-1 remainder — Track A's half; Track B's inventory half is validated above)
- [ ] Cloud hosting reachable via URL for TAs/instructor (R2-3)
- [ ] Project board with all features + initial work items (user stories, tech debt, research items) (R1-2)
- [ ] High-level architecture sketch (R1-3)
- [ ] Password reset via the existing Forgot Password flow (STRETCH-01)
- [ ] Custom storage locations beyond Pantry/Fridge/Freezer (STRETCH-02)

### Backlog / Research Items (explicitly NOT in this PoC's committed scope)

Captured from the household's full product vision — real value, but each requires hardware sensors, ML modeling, or third-party integrations beyond a semester PoC. Tracked as research items on the board so the team can spike/prototype opportunistically without committing rubric-critical time to them:

- Automatic inventory capture via RFID tags, barcode scanning, shelf weight sensors, fridge cameras, and receipt/email parsing
- Consumption detection (distinguish eaten vs. discarded vs. moved to another container) — currently a manual user action instead
- True spoilage prediction using storage temperature, humidity, package status, and food-specific shelf-life models — MVP uses a flat best-by-date comparison instead
- Meal planning recommendations based on what will spoil first, dietary restrictions, cook time, servings
- Waste analytics and purchase-quantity/schedule suggestions
- Automated purchasing / grocery list generation / reordering with duplicate-avoidance
- Safety monitoring: refrigeration-failure temperature alerts, food-left-out timers, product recall lookups
- Per-person behavior adaptation (e.g., learning typical consumption rates, ignored leftovers)

### Out of Scope

- OAuth / third-party login — assignment scope is username/password only; SN1 only requires "secure user accounts"
- Real-time multi-user live sync (e.g. websockets) — refresh-based updates are sufficient for the PoC
- Mobile app — web-only PoC per SR2
- Any physical sensor/hardware integration (RFID readers, cameras, scales) — no hardware budget or timeline for this course project; see Backlog above
- Billing/payment — not a stakeholder need

## Context

- This is a graded academic team project (MIS385N Advanced Programming & App Development), delivered in phases with a shared grading rubric (`Team Project_Fa26.pdf`).
- Phase 1 (5 pts, due first) requires: all features + initial work items on a board, a high-level sketch of the app, and a stated tool/approach choice — plus a separate Project Plan (team members, sprint cadence, collaboration tools, methodology, toolchain), which is **owned by another team member and out of scope for this document**.
- Phase 2 (10 pts) requires all General Requirements satisfied: hardware resources (here: food item stock) stored in DB with an API, user/household info accessible from the app with no hard-coded data, and the app hosted on the cloud and reachable via URL.
- General requirements apply across all phases: issue tracker kept separate from the user-story board, all user stories defined by end of Phase 1 (refined later), each user story describable in ≤3 sentences.
- The assignment's "HWSet1/HWSet2, capacity/availability, request/checkout/check-in" UI mockup (Figures 2–3) maps directly onto per-item food stock: capacity = total units currently stocked of that item, availability = units not yet reserved or consumed.
- Existing scaffold is a bare-bones starter template (routes stubbed, DB helper modules stubbed) — not yet wired to a real MongoDB instance, no encryption implemented, no tests, no deployment config, and still named/labeled generically ("project", "hardware set") — will be relabeled conceptually as household/food-item work proceeds.

## Constraints

- **Tech stack**: Flask + MongoDB + React — matches the existing scaffold (stack choice/toolchain is documented in the separate Project Plan)
- **Process**: User stories must be ≤3 sentences (Mountain Goat Software style); issues (bugs/improvements) tracked separately from user-story board, not combined
- **Security**: Userid and password must be encrypted at rest/in transit (SR3) — non-negotiable rubric item
- **Domain simplification**: No physical sensors are available or in scope — all inventory capture (adding/removing/reserving items) is manual user input via the web UI, not automated detection

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build on existing `server/`/`client/` scaffold rather than starting fresh | Scaffold already encodes the assignment's expected route surface and DB module boundaries | — Pending |
| Reframe the app as a household food inventory system, with "hardware resources" = food item stock | User's stated product vision; capacity/availability/checkout/check-in map cleanly onto stocked food items and satisfy SN1–SN6 as-is | ✓ Good |
| Split the household's full product vision into MVP (manual inventory + reserve/consume/restock) vs. Backlog/Research (sensors, ML spoilage/consumption detection, meal planning, purchasing, safety, behavior learning) | Full vision requires hardware sensors, ML models, and third-party integrations not achievable in a semester PoC; MVP still fully satisfies SN1–SN6, backlog items become the board's "research items" (R1-2) | ✓ Good |
| Skip formal research phase (stack/features/architecture) | Assignment PDF fully specifies stakeholder needs, requirements, and recommended stack — external research adds no value here | ✓ Good |
| Skip codebase-mapping subagent | Existing scaffold is small (4 backend files, handful of React pages); read directly instead of spawning a mapper | ✓ Good |
| Inventory items live in a separate `Items` collection, not embedded in the household document (Track B execution checkpoint, one-way door) | Removes the Track A/Track B write-contention risk the roadmap had flagged; makes the overbooking guard a single conditional update instead of a nested-array update | ✓ Good |
| Each restock is its own batch (not a running-total overwrite); item identity resolved via case/whitespace normalization + substring/prefix matching, ambiguous matches create a new item rather than guessing (CONTEXT.md D-01/D-03) | Preserves per-purchase dates for FIFO consumption and accurate freshness; avoids silently merging distinct items (e.g. "milk" into "milk chocolate") | ✓ Good |
| Reserve is an unenforced "dibs" flag, never a hold on stock; consume always draws from total available regardless of reservations (CONTEXT.md D-04–D-08) | Matches real household trust dynamics — reservation is a coordination signal between housemates, not an access-control mechanism | ✓ Good |
| Freezer freshness is a quality-decay signal computed from purchase date (not a food-safety best-by comparison like Pantry/Fridge) (CONTEXT.md D-11) | Frozen food doesn't spoil the way fridge/pantry food does; a flat best-by model would be factually wrong for that location | ✓ Good |
| Track B's tracer plan (02-01) bootstrapped the React client (`package.json`, Vite) and fixed Flask's broken imports, since neither existed/worked before this phase | The scaffold could not run at all — no track could proceed without this; flagged as a cross-track coordination point so other tracks build into the same shell | ✓ Good |

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
*Last updated: 2026-09-22 after Track B (Inventory Management) phase completion — 5/5 UAT tests passed, 4/4 plans executed*
