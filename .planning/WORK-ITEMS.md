# PantryTrack — Feature Board & Initial Work Items (R1-2)

**Board (visual):** https://claude.ai/code/artifact/f0a9abd4-7299-49bd-87c5-e400d61a4fcc

This is the source-of-truth for the Phase 1 rubric item R1-2 ("All Features on a board. Initial work items — user stories, technical debt, or research items — created for features"). If the team also maintains a GitHub Projects board, import these cards there and keep it as the canonical issue-tracker-adjacent board (kept **separate** from the bug/issue tracker per the assignment's General Requirements).

Each user story is ≤3 sentences per the Mountain Goat Software convention referenced in the assignment.

## Legend

- **User story** — an observable thing a household member can do
- **Technical debt** — engineering work with no direct user-facing story (implementation, infra, security)
- **Research item** — a spike/backlog item from the household's full product vision, explicitly **not committed** for this PoC

---

## 1. Account & Authentication — Phase 1 / Track A

**Goal:** A user can create a secure account and stay signed in while using the app.

| ID | Type | Title | Story / Description | Req |
|----|------|-------|----------------------|-----|
| US-01 | User story | Sign up | As a new household member, I want to create an account with a userid and password so I can access my household's inventory. | ACCT-02 |
| US-02 | User story | Sign in | As a returning user, I want to sign in with my credentials so I can resume managing my household's food inventory. | ACCT-01 |
| TD-01 | Technical debt | Encrypt credentials | Add password hashing (e.g. bcrypt) in `usersDatabase.py` — currently a stub with no security logic. | ACCT-03 |
| TD-02 | Technical debt | Persist session | Implement session/token handling so login state survives page navigation — not implemented in the scaffold. | ACCT-04 |

## 2. Household Management — Phase 1 / Track A

**Goal:** A user can create or join the shared household space their food inventory lives in.

| ID | Type | Title | Story / Description | Req |
|----|------|-------|----------------------|-----|
| US-03 | User story | Create a household | As a user, I want to create a new household with a name, description, and ID so my family or roommates share one inventory. | HH-01 |
| US-04 | User story | Join a household | As a user, I want to join an existing household using its ID so I see the same inventory as my housemates. | HH-02 |
| US-05 | User story | View my households | As a user, I want to see every household I belong to so I can switch between them if I'm part of more than one. | HH-03 |
| TD-03 | Technical debt | Household item-stock schema | Agree on and define the household document's item-stock shape (capacity/availability per item, keyed by location) before Inventory work starts writing to it. **Coordination point between Track A and Track B.** | HH-01 |

## 3. Inventory Management — Phase 2 / Track B

**Goal:** A household member can see what food is on hand and move it through reserve → consume, or add new stock.

| ID | Type | Title | Story / Description | Req |
|----|------|-------|----------------------|-----|
| US-06 | User story | View inventory by location | As a household member, I want to see items grouped by Pantry, Fridge, and Freezer with capacity and availability so I know what's on hand at a glance. | INV-01 |
| US-07 | User story | Restock an item | As a household member, I want to log a new purchase with quantity, purchase date, and best-by date so the inventory reflects what I bought. | INV-02 |
| US-08 | User story | Reserve an item | As a household member, I want to reserve a quantity of an item for myself so others know not to use it before I do. | INV-03 |
| US-09 | User story | Consume an item | As a household member, I want to mark a quantity as consumed so the inventory count stays accurate. | INV-04 |
| US-10 | User story | See freshness at a glance | As a household member, I want to see whether an item is fresh, expiring soon, or expired so I know what to use first. | INV-05 |
| TD-04 | Technical debt | Overbooking guard | Reject checkout/reserve requests that exceed current availability — no validation logic exists yet in the scaffold. | INV-04 |

## 4. Data Integration & API — Phase 3 / Track C

**Goal:** Everything on screen comes from a live database through a real API — nothing is hard-coded.

| ID | Type | Title | Story / Description | Req |
|----|------|-------|----------------------|-----|
| US-11 | User story | Always-live data | As a household member, I want everything I see to reflect the real shared database, never sample data, so I can trust the app for real grocery use. | DATA-03 |
| TD-05 | Technical debt | Wire REST endpoints | Implement the stubbed Flask routes in `app.py` against real DB module logic — routes currently exist but do nothing. | DATA-02 |
| TD-06 | Technical debt | Remove hard-coded frontend data | Replace placeholder/sample values in React components (`Project.js`, `Checkout.js`, `MyUserPortal.js`) with live API calls. | DATA-01 |
| TD-07 | Technical debt | Provision MongoDB Atlas | Stand up a MongoDB Atlas cluster and connection config via environment variables — no secrets committed to the repo. | DATA-01 |

## 5. Deployment & Quality — Phase 3 / Track C

**Goal:** The PoC is reachable by the instructor/TAs and its core flows are covered by automated tests.

| ID | Type | Title | Story / Description | Req |
|----|------|-------|----------------------|-----|
| US-12 | User story | Reachable, gradeable app | As an instructor or TA, I want to open a public URL and walk through the full account → household → inventory flow so I can grade the working PoC. | OPS-01 |
| TD-08 | Technical debt | Deployment pipeline | Set up cloud hosting and deploy config so the app is reachable via a stable public URL. | OPS-01 |
| TD-09 | Technical debt | Backend test harness | Set up PyTest and write coverage for login, create/join household, reserve, consume, and restock routes. | OPS-02 |
| TD-10 | Technical debt | Retire generic naming | As implementation lands, rename the scaffold's generic "project"/"hardware set" language to household/food-item domain terms so code and UI stay legible. | — |

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

**Totals:** 5 committed features · 12 user stories · 10 technical debt items · 10 research items · 17/17 v1 requirements covered.

**Out of scope reminder:** The Project Plan (team members, sprint cadence, collaboration tools, methodology, toolchain — R1-1) is a separate deliverable owned by another team member and is not represented on this board.

---
*Board created: 2026-09-14*
