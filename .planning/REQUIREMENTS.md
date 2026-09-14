# Requirements: HaaS PoC (Group 2 Monday)

**Defined:** 2026-09-14
**Core Value:** A user can securely log in, join or create a project, and check hardware resources out of and back into a live, database-backed inventory — with no hard-coded data anywhere in the app.

Source: `Team Project_Fa26.pdf` (Stakeholder Needs SN0–SN6, System Requirements SR1–SR5, MVP feature spec for User Management / Resource Management).

## v1 Requirements

### Account (SN1, SR3, SR4)

- [ ] **ACCT-01**: User can sign in with userid and password
- [ ] **ACCT-02**: User can click "New User" to open a sign-up form and create a userid/password
- [ ] **ACCT-03**: Userid and password are encrypted (not stored or transmitted in plaintext)
- [ ] **ACCT-04**: User session persists across page navigation within the app

### Project (SN1, SR4, SR5)

- [ ] **PROJ-01**: User can create a new project by providing name, description, and projectID
- [ ] **PROJ-02**: User can join/access an existing project by entering its projectID
- [ ] **PROJ-03**: User can view the list of projects they belong to

### Hardware Resources (SN2, SN3, SN4, SN5, SR5)

- [ ] **HW-01**: User can view total capacity of HWSet1 and HWSet2
- [ ] **HW-02**: User can view current availability of HWSet1 and HWSet2
- [ ] **HW-03**: User can request/checkout a chosen quantity of a hardware set into their project
- [ ] **HW-04**: User can check in previously checked-out hardware units back to the shared pool
- [ ] **HW-05**: Checkout/check-in updates availability immediately and consistently (no overbooking beyond capacity)

### Data & API (SR2, SR5, R2-1, R2-2)

- [ ] **DATA-01**: User, project, and hardware data are persisted in MongoDB — no hard-coded data on any page
- [ ] **DATA-02**: A REST API layer exposes user/project/hardware operations to the React frontend
- [ ] **DATA-03**: Frontend renders all displayed values (capacity, availability, project list, project details) from live API responses

### Deployment & Quality (SN6, SR1, R2-3, SN0)

- [ ] **OPS-01**: App is deployed to a cloud host and reachable via a public URL for TAs/instructor
- [ ] **OPS-02**: Automated tests (PyTest) cover core backend routes (login, create/join project, checkout, check-in)
- [ ] **OPS-03**: Project plan documents team members, sprint velocity, collaboration tools, and methodology (R1-1)

## v2 Requirements

Deferred — acknowledged as possible extensions but not committed for this milestone.

### Enhancements

- **ENH-01**: Password reset / "Forgot Password" flow (scaffold page `ForgotMyPassword.js` exists but not required by stakeholder needs)
- **ENH-02**: Admin view to create new hardware sets beyond HWSet1/HWSet2 (`create_hardware_set` route exists in scaffold)
- **ENH-03**: Usage/checkout history per project
- **ENH-04**: Reliability/quality metrics dashboard (SN0 beyond basic testing)

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth / third-party login | Not required by SN1; adds complexity beyond PoC scope |
| Real-time multi-user collaboration on a project | Not a stated stakeholder need |
| Mobile app | SR2 specifies a web front-end only |
| Billing / payment processing | HaaS/XaaS framing is context, not a stakeholder need — PoC stops at resource lifecycle |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ACCT-01..04 | TBD (roadmap) | Pending |
| PROJ-01..03 | TBD (roadmap) | Pending |
| HW-01..05 | TBD (roadmap) | Pending |
| DATA-01..03 | TBD (roadmap) | Pending |
| OPS-01..03 | TBD (roadmap) | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 19 ⚠ (resolved by `/gsd-new-project` roadmap step)

---
*Requirements defined: 2026-09-14*
*Last updated: 2026-09-14 after initial definition*
