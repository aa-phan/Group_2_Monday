# PantryTrack — Feature Board & Initial Work Items (R1-2)

**Board (visual):** https://claude.ai/code/artifact/f0a9abd4-7299-49bd-87c5-e400d61a4fcc

This is the source-of-truth for the Phase 1 rubric item R1-2 ("All Features on a board. Initial work items — user stories, technical debt, or research items — created for features"). If the team also maintains a GitHub Projects board, import these cards there and keep it as the canonical issue-tracker-adjacent board (kept **separate** from the bug/issue tracker per the assignment's General Requirements).

Each user story is ≤3 sentences per the Mountain Goat Software convention referenced in the assignment.

## Legend

- **User story** — an observable thing a household member can do
- **Technical debt** — engineering work with no direct user-facing story (implementation, infra, security)
- **Research item** — a spike/backlog item from the household's full product vision, explicitly **not committed** for this PoC
- **Sub-story** — a separately demonstrable behavior of a parent story, numbered with its parent's ID plus a letter (e.g. `US-07a`)

---

## 1. Account & Authentication — Track A

**Goal:** A user can create a secure account and stay signed in while using the app.

**Rubric ownership:** R1-1 (Project Plan) · R2-2 (live user/household data, no hard-coding)

| ID | Type | Title | Story / Description | Req | Phase |
|----|------|-------|----------------------|-----|-------|
| TD-DOC-A | Technical debt | Define Track A scope, schema, and initial stories | Define the account/household data model (userid/password fields, household document shape with name/description/householdID) and write Track A's initial user stories (US-01..US-05) for the feature board. | ACCT/HH | 1 |
| US-R1-A | User story | Document the project plan | As the instructor, I want a documented project plan covering team members, sprint velocity, collaboration tools, and implementation methodology so I can assess how the team is organized and working together. | R1-1 | 1 |
| US-01 | User story | Sign up | As a new household member, I want to create an account with a userid and password so I can access my household's inventory. | ACCT-02 | 2 |
| US-02 | User story | Sign in | As a returning user, I want to sign in with my credentials so I can resume managing my household's food inventory. | ACCT-01 | 2 |
| TD-01 | Technical debt | Encrypt credentials | Add password hashing (e.g. bcrypt) in `usersDatabase.py` — currently a stub with no security logic. | ACCT-03 | 2 |
| TD-02 | Technical debt | Persist session | Implement session/token handling so login state survives page navigation — not implemented in the scaffold. | ACCT-04 | 2 |

## 2. Household Management — Track A

**Goal:** A user can create or join the shared household space their food inventory lives in.

**Part of:** Track A — see Rubric ownership in section 1.

| ID | Type | Title | Story / Description | Req | Phase |
|----|------|-------|----------------------|-----|-------|
| US-03 | User story | Create a household | As a user, I want to create a new household with a name, description, and ID so my family or roommates share one inventory. | HH-01 | 2 |
| US-04 | User story | Join a household | As a user, I want to join an existing household using its ID so I see the same inventory as my housemates. | HH-02 | 2 |
| US-05 | User story | View my households | As a user, I want to see every household I belong to so I can switch between them if I'm part of more than one. | HH-03 | 2 |
| TD-03 | Technical debt | Household item-stock schema | Agree on and define the household document's item-stock shape (capacity/availability per item, keyed by location) before Inventory work starts writing to it. **Coordination point between Track A and Track B.** | HH-01 | 2 |

## 3. Inventory Management — Track B

**Goal:** A household member can see what food is on hand and move it through reserve → consume, or add new stock.

**Rubric ownership:** R1-2 (Feature board) · R2-1 (food-item resources in DB + API)

**Schema note:** Track B's item-stock shape is settled in `.planning/phases/02-inventory-management/02-CONTEXT.md` (decisions D-01 through D-11). Each restock is its own batch with its own purchase and best-by dates; an item's capacity is the sum of its batch quantities; item identity is a normalized name within a single location.

| ID | Type | Title | Story / Description | Req | Phase |
|----|------|-------|----------------------|-----|-------|
| TD-DOC-B | Technical debt | Define Track B scope, schema, and initial stories | Define the household item-stock schema — items keyed by Pantry/Fridge/Freezer location, each holding a list of batches with their own quantity, purchase date, and best-by date, with capacity and availability derived as sums — and write Track B's initial user stories for the feature board. Delivered as `02-CONTEXT.md` (decisions D-01..D-11) plus the four phase plans `02-01` through `02-04`. | INV | 1 |
| US-R1-B | User story | Publish the feature board | As the instructor, I want to see every planned feature captured as user stories, technical debt, or research items on a shared board so I can verify the team has scoped its work before implementation begins. | R1-2 | 1 |
| US-06 | User story | View inventory by location | As a household member, I want to see items grouped by Pantry, Fridge, and Freezer with each item's capacity and availability so I know what's on hand at a glance. Availability is what nobody has claimed yet; capacity is what is physically there. A location with nothing in it says so plainly rather than showing a blank space. | INV-01 | 2 |
| US-06a | User story | See an item's batch history | As a household member, I want to open an item and see each shopping trip that went into it — its quantity, purchase date, and best-by date — so I can tell fresh stock apart from older stock of the same food. The batches are listed in the order they will be used up. | INV-01 | 2 |
| US-07 | User story | Restock an item | As a household member, I want to log a new purchase with a quantity, a purchase date, and a best-by date so the inventory reflects what I bought. Each purchase is recorded as its own batch rather than being folded into a running total, so the dates stay attached to the units they belong to. | INV-02 | 2 |
| US-07a | User story | Restock the same food again | As a household member, I want a second purchase of something I already have to add to that item instead of creating a duplicate row, even if I typed the name slightly differently. Matching ignores capitalisation and extra spaces and allows one name to contain the other, but only within the same location — Milk in the Fridge and Milk in the Freezer stay separate. | INV-02 | 2 |
| US-07b | User story | Be told when a name is ambiguous | As a household member, I want the app to create a separate item rather than guess when the name I typed could match two things I already have, and to tell me which two. That way it never silently merges my milk into my milk chocolate. | INV-02 | 2 |
| US-08 | User story | Reserve an item | As a household member, I want to claim a quantity of an item under my name so my housemates know I'm planning to use it. Claiming is a heads-up, not a hold — it never takes the food out of the shared count and never stops anyone else from taking it. | INV-03 | 2 |
| US-08a | User story | Release a claim I made | As a household member, I want to take back a claim I made once I no longer need it, so the item stops showing as spoken for. Only the person who made a claim can release it. | INV-03 | 2 |
| US-08b | User story | See who claimed what | As a household member, I want to see which housemate has claimed a quantity of an item and how much, so I can decide for myself whether to take it anyway or leave it for them. | INV-03 | 2 |
| US-09 | User story | Consume an item | As a household member, I want to log a quantity as used so the inventory count stays accurate. I can do this at any time without claiming it first — grabbing a cup of milk is just a consume. | INV-04 | 2 |
| US-09a | User story | Use the soonest-expiring stock first | As a household member, I want what I consume to come off the batch closest to its date first, spilling into newer stock only when that batch runs out, so the food most likely to go to waste is the food that gets used. | INV-04 | 2 |
| US-10 | User story | See freshness at a glance | As a household member, I want every item to carry a freshness flag worked out from its own dates against today, so I know what to use first. The flag is a plain date comparison — no sensors, no predictions. | INV-05 | 2 |
| US-10a | User story | Pantry freshness | As a household member, I want a pantry item to simply read as fresh until its best-by date passes, with no early warning, because dry staples don't need me chased about them a week out. | INV-05 | 2 |
| US-10b | User story | Fridge freshness | As a household member, I want a fridge item to warn me when it's within three days of its best-by date, and to read as past its date once that day has gone by, so I get a useful window to actually cook it. | INV-05 | 2 |
| US-10c | User story | Freezer quality signal | As a household member, I want a freezer item judged on how long it has been frozen — good under six months, declining from six to twelve, freezer-burn risk beyond that — because frozen food loses quality rather than becoming unsafe. The flag is worked out from the freeze date, and it never tells me to throw food away. | INV-05 | 2 |
| TD-04 | Technical debt | Overbooking guard | Reject a consume that would take more units than the item physically holds, leaving the item completely unchanged when it does — no partial deduction. The guard applies to consume only; a claim is never rejected, because a claim was never a real hold on the food. | INV-04 | 2 |
| TD-04a | Technical debt | Concurrent consumes | Make two simultaneous consumes of the same item unable to drive its count below zero: apply each consume with a conditional update pinned to the exact counts that were read, and have the losing writer re-check the guard before retrying. | INV-04 | 2 |
| TD-11 | Technical debt | Bootstrap the React client | Stand up the React application — `package.json`, build tooling, entry HTML, and root component — since `client/` currently has no package manifest and every source file is empty. **Cross-track coordination point: Track B creates this shell first because its inventory view needs it; Tracks A, C, and D build into the same shell rather than creating a second one.** | — | 2 |
| TD-12 | Technical debt | Make the Flask app runnable | Fix `server/app.py`'s three module imports, which name modules that do not exist and stop the app from starting at all, and add the `requirements.txt` and virtual environment the repository currently lacks. Replace the placeholder connection-string literal with an environment-variable read — the credential half of this overlaps Track C's TD-07, which owns provisioning. | — | 2 |

## 4. Data Integration & API — Track C

**Goal:** Everything on screen comes from a live database through a real API — nothing is hard-coded.

**Rubric ownership:** R1-4 (Tool choice & approach) · Stretch Features (US-13, US-14) in place of a numbered R2 item

| ID | Type | Title | Story / Description | Req | Phase |
|----|------|-------|----------------------|-----|-------|
| TD-DOC-C | Technical debt | Define Track C scope, schema, and initial stories | Define the REST API surface and deployment/test plan covering DATA-01..03 and OPS-01..02, and write Track C's initial user stories (US-11..US-12) for the feature board. | DATA/OPS | 1 |
| US-R1-C | User story | Document tool choice & approach | As the instructor, I want a written explanation of the team's chosen tech stack and technical approach so I can evaluate whether the decisions fit the project's needs. | R1-4 | 1 |
| US-11 | User story | Always-live data | As a household member, I want everything I see to reflect the real shared database, never sample data, so I can trust the app for real grocery use. | DATA-03 | 2 |
| TD-05 | Technical debt | Wire REST endpoints | Implement the stubbed Flask routes in `app.py` against real DB module logic — routes currently exist but do nothing. | DATA-02 | 2 |
| TD-06 | Technical debt | Remove hard-coded frontend data | Replace placeholder/sample values in React components (`Project.js`, `Checkout.js`, `MyUserPortal.js`) with live API calls. | DATA-01 | 2 |
| TD-07 | Technical debt | Provision MongoDB Atlas | Stand up a MongoDB Atlas cluster and connection config via environment variables — no secrets committed to the repo. | DATA-01 | 2 |
| US-13 | User story | Reset a forgotten password | As a user who forgot their password, I want to reset it via the existing Forgot Password flow so I can regain access to my household's inventory without contacting an admin. | STRETCH-01 | 2 |
| US-14 | User story | Manage custom storage locations | As a household member, I want to define storage locations beyond the default Pantry/Fridge/Freezer (e.g. a garage freezer or wine fridge) so my household's inventory reflects how we actually store food. | STRETCH-02 | 2 |

## 5. Deployment & Quality — Track D

**Goal:** The PoC is reachable by the instructor/TAs and its core flows are covered by automated tests.

**Rubric ownership:** R1-3 (High-level sketch) · R2-3 (Cloud deployment)

| ID | Type | Title | Story / Description | Req | Phase |
|----|------|-------|----------------------|-----|-------|
| TD-DOC-D | Technical debt | Define Track D scope, schema, and initial stories | Define the deployment pipeline and test-coverage plan covering OPS-01/OPS-02, and write Track D's initial user stories (US-12) for the feature board. | OPS | 1 |
| US-R1-D | User story | Sketch the application architecture | As the instructor, I want a high-level sketch of the application's architecture and user flow so I can quickly understand the system's design before reviewing the code. | R1-3 | 1 |
| US-12 | User story | Reachable, gradeable app | As an instructor or TA, I want to open a public URL and walk through the full account → household → inventory flow so I can grade the working PoC. | OPS-01 | 2 |
| TD-08 | Technical debt | Deployment pipeline | Set up cloud hosting and deploy config so the app is reachable via a stable public URL. | OPS-01 | 2 |
| TD-09 | Technical debt | Backend test harness | Set up PyTest and write coverage for login, create/join household, reserve, consume, and restock routes. | OPS-02 | 2 |
| TD-10 | Technical debt | Retire generic naming | As implementation lands, rename the scaffold's generic "project"/"hardware set" language to household/food-item domain terms so code and UI stay legible. | — | 2 |

## Future Vision — Research Backlog (not scheduled, v2)

The household's full product vision, beyond this PoC's committed scope — each needs hardware sensors, ML modeling, or third-party integrations no semester project can fund. Kept visible so the team can spike opportunistically without risking rubric-critical time.

| ID | Type | Title | Description | Req |
|----|------|-------|--------------|-----|
| R-01 | Research | RFID / barcode auto-capture | Spike whether RFID tags or barcode scans can auto-detect items entering or leaving storage. | CAP-01, CAP-02 |
| R-02 | Research | Fridge camera + computer vision | Spike using a fridge-mounted camera and a CV model to identify items without manual entry. | CAP-04 |
| R-03 | Research | Shelf / fridge weight sensors | Spike weight-sensor shelving to detect quantity changes automatically. | CAP-03 |
| R-04 | Research | Receipt / email scanning | Research parsing grocery receipts or order emails to auto-populate restocked items. | CAP-05 |
| R-05 | Research | Real spoilage prediction | Research shelf-life models driven by storage temperature, humidity, and package status, per food type. | INT-02 |
| R-06 | Research | Consumption detection | Research heuristics to distinguish "eaten" from "discarded" from "moved to another container." | INT-01 |
| R-07 | Research | Per-person behavior learning | Research learning individual consumption patterns to personalize recommendations. | INT-03 |
| R-08 | Research | Meal planning engine | Research a recommendation algorithm using what's about to spoil, dietary restrictions, cook time, servings. | PLAN-01 |
| R-09 | Research | Waste analytics & auto-purchasing | Research surfacing repeat-waste patterns and connecting to grocery APIs for reordering. | PLAN-02, PLAN-03 |
| R-10 | Research | Food safety alerting | Research refrigeration-failure alerts, "left out too long" timers, and recall lookups. | SAFE-01, SAFE-02, SAFE-03 |

---

**Totals:** 5 committed features · 18 user stories (9 with sub-stories — 9 additional sub-story rows under Track B) · 17 technical debt items (13 Phase 2 + 4 Phase 1 scope/schema/stories items) · 10 research items · 19/19 v1 requirements covered.

**4 tracks, 4 developers:** Track A, Track B, Track C, and Track D each own exactly one Phase 1 rubric item (US-R1-A/B/C/D → R1-1/R1-2/R1-4/R1-3 respectively) plus either one Phase 2 rubric item or, for Track C, a promoted stretch-feature scope (US-13, US-14) in place of a numbered R2 item.

**Out of scope reminder:** The Project Plan (team members, sprint cadence, collaboration tools, methodology, toolchain — R1-1) is now represented on this board via US-R1-A, owned by Track A.

---
*Board created: 2026-09-14*
