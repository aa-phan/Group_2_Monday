# Requirements: PantryTrack — Household Food Inventory PoC (Group 2 Monday)

**Defined:** 2026-09-14 (re-scoped from generic hardware domain to household food inventory domain)
**Core Value:** A household member can see what food the household has across pantry/fridge/freezer, reserve or consume items, and restock — all from live shared data, with no hard-coded values anywhere in the app.

Source: `Team Project_Fa26.pdf` (Stakeholder Needs SN0–SN6, System Requirements SR1–SR5, MVP feature spec for User Management / Resource Management), reframed onto a household food inventory: household = "project", food item stock = "hardware resource".

## v1 Requirements

### Account (SN1, SR3)

- [ ] **ACCT-01**: User can sign in with userid and password
- [ ] **ACCT-02**: User can click "New User" to open a sign-up form and create a userid/password
- [ ] **ACCT-03**: Userid and password are encrypted (not stored or transmitted in plaintext)
- [ ] **ACCT-04**: User session persists across page navigation within the app

### Household (SN1, SR4, SR5)

- [ ] **HH-01**: User can create a new household by providing name, description, and householdID
- [ ] **HH-02**: User can join/access an existing household by entering its householdID
- [ ] **HH-03**: User can view the list of households they belong to

### Inventory (SN2, SN3, SN4, SN5, SR5)

- [ ] **INV-01**: User can view all food items in a household's inventory, grouped by location (Pantry / Fridge / Freezer), each showing capacity (total units stocked) and availability (units not yet reserved or consumed)
- [ ] **INV-02**: User can restock an item — add a quantity with a purchase date and a best-by/expiration date ("check-in")
- [ ] **INV-03**: User can reserve/claim a quantity of an item for themselves without removing it from inventory ("request")
- [ ] **INV-04**: User can consume/remove a quantity of an item from inventory ("checkout"), and the action is rejected if it would exceed what's currently available
- [ ] **INV-05**: Each item displays a simple freshness flag (fresh / expiring soon / expired) computed from its best-by date vs. today — no sensor or ML input required

### Data & API (SR2, SR5, R2-1, R2-2)

- [ ] **DATA-01**: User, household, and food-item data are persisted in MongoDB — no hard-coded data on any page
- [ ] **DATA-02**: A REST API layer exposes user/household/inventory operations to the React frontend
- [ ] **DATA-03**: Frontend renders all displayed values (capacity, availability, household list, item details, freshness flags) from live API responses

### Deployment & Quality (SN6, SR1, R2-3, SN0)

- [ ] **OPS-01**: App is deployed to a cloud host and reachable via a public URL for TAs/instructor
- [ ] **OPS-02**: Automated tests (PyTest) cover core backend routes (login, create/join household, reserve, consume, restock)

> Note: R1-1 (Project Plan — team members, sprint cadence, collaboration tools, methodology, toolchain) is a separate deliverable owned by another team member and is intentionally out of scope here.

## v2 Requirements

Deferred — acknowledged as valuable but out of committed scope for this PoC. These require hardware sensors, ML modeling, or third-party integrations not achievable in a semester project; several are natural candidates for research spikes on the board rather than committed user stories.

### Automated Capture

- **CAP-01**: RFID tag scanning to auto-detect items entering/leaving storage
- **CAP-02**: Barcode scanning for quick item entry
- **CAP-03**: Shelf/fridge weight sensors to detect quantity changes automatically
- **CAP-04**: Fridge camera + computer vision to identify items without manual entry
- **CAP-05**: Receipt/email scanning to auto-populate restocked items

### Intelligent Tracking

- **INT-01**: Consumption detection — distinguish "eaten" vs. "discarded" vs. "moved to another container" (MVP treats all removals as a single manual "consume" action)
- **INT-02**: True spoilage prediction using storage temperature, humidity, package status, and food-specific shelf-life models (MVP uses a flat best-by-date comparison)
- **INT-03**: Per-person behavior adaptation (e.g., learned consumption rate, frequently-ignored leftovers) driving smarter recommendations

### Planning & Purchasing

- **PLAN-01**: Meal planning recommendations based on what will spoil first, dietary restrictions, cook time, and servings needed
- **PLAN-02**: Waste analytics — surface repeatedly discarded items and suggest smaller/adjusted purchase quantities
- **PLAN-03**: Automated grocery list generation / staple reordering with duplicate-purchase avoidance

### Safety

- **SAFE-01**: Refrigeration-failure and temperature-excursion alerts
- **SAFE-02**: "Food left out too long" timers/alerts
- **SAFE-03**: Product recall lookups against scanned/logged items

### Enhancements (from prior scoping pass, still applicable)

- **ENH-01**: Password reset / "Forgot Password" flow (scaffold page `ForgotMyPassword.js` exists but not required by stakeholder needs)
- **ENH-02**: Admin view to define new food item categories/locations beyond Pantry/Fridge/Freezer

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth / third-party login | Not required by SN1; adds complexity beyond PoC scope |
| Real-time multi-user live sync (websockets) | Not a stated stakeholder need; refresh-based updates suffice |
| Mobile app | SR2 specifies a web front-end only |
| Any physical sensor/hardware integration | No hardware budget/timeline for a course project — see v2 Automated Capture items instead |
| Billing / payment processing | Not a stakeholder need |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ACCT-01 | Phase 1 | Pending |
| ACCT-02 | Phase 1 | Pending |
| ACCT-03 | Phase 1 | Pending |
| ACCT-04 | Phase 1 | Pending |
| HH-01 | Phase 1 | Pending |
| HH-02 | Phase 1 | Pending |
| HH-03 | Phase 1 | Pending |
| INV-01 | Phase 2 | Pending |
| INV-02 | Phase 2 | Pending |
| INV-03 | Phase 2 | Pending |
| INV-04 | Phase 2 | Pending |
| INV-05 | Phase 2 | Pending |
| DATA-01 | Phase 3 | Pending |
| DATA-02 | Phase 3 | Pending |
| DATA-03 | Phase 3 | Pending |
| OPS-01 | Phase 3 | Pending |
| OPS-02 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17 (Phase 1: 7, Phase 2: 5, Phase 3: 5)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-14*
*Last updated: 2026-09-14 after roadmap creation (3-phase parallel-track structure)*
