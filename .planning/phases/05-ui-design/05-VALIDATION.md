---
phase: "05"
slug: "ui-design"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-24"
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None detected — `client/package.json` has no test runner, no `*.test.*`/`*.spec.*` files exist anywhere under `client/` |
| **Config file** | none — Wave 0 N/A, no framework installed for this phase (out of scope) |
| **Quick run command** | N/A — no framework installed |
| **Full suite command** | N/A — no framework installed |
| **Estimated runtime** | N/A |

---

## Sampling Rate

- **After every task commit:** N/A — no automated quick-run command exists for this phase's domain (visual/doc changes); rely on manual visual check per task
- **After every plan wave:** Manual visual check at ≤599px and ≥600px viewport widths; manual doc-presence check against the 5 Success Criteria
- **Before `/gsd-verify-work`:** All 5 Success Criteria manually verified true
- **Max feedback latency:** N/A (manual verification, no automated suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-TBD | 01 | 1 | SC-1 | — | N/A (presentation-only, no new attack surface) | manual (visual) | N/A — resize to ≤599px, confirm card layout, no horizontal scroll | ❌ Wave 0 N/A | ⬜ pending |
| 05-01-TBD | 01 | 1 | SC-2 | — | N/A | manual (visual) | N/A — visual inspection against token palette in `05-DESIGN.md` | ❌ Wave 0 N/A | ⬜ pending |
| 05-01-TBD | 01 | 1 | SC-3 | — | N/A | manual (doc review) | N/A — confirm `App.js` documents `householdId`/`userId`/`userName` contract | ❌ Wave 0 N/A | ⬜ pending |
| 05-01-TBD | 01 | 1 | SC-4 | — | N/A | manual (doc review) | N/A — confirm JSDoc block above each of the 6 components' signatures | ❌ Wave 0 N/A | ⬜ pending |
| 05-01-TBD | 01 | 1 | SC-5 | — | N/A | manual (doc + visual) | N/A — confirm `:root` custom properties in `index.css`, documented in `05-DESIGN.md` | ❌ Wave 0 N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Task IDs are placeholders (TBD) pending the planner's actual task numbering — update this map once PLAN.md exists.*

---

## Wave 0 Requirements

*None: this phase has no REQ-IDs (board items use `DESIGN` in place of a requirement ID) and its 5 Success Criteria are inherently visual/documentation checks, not logic under test. Installing a client-side test framework (Jest/Vitest/Testing Library) to automate them is explicitly out of scope for this phase's locked decisions (D-01–D-08) — flagged as a known gap, not a blocker.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Inventory view has clear visual grouping/spacing, usable at phone width | SC-1 | No visual-regression tooling exists; out of scope to add for this PoC | Resize browser / DevTools device toolbar to ≤599px width; confirm card layout renders, no horizontal scroll, no bare HTML table |
| Freshness badges use consistent, recognizable color coding | SC-2 | Visual/perceptual judgment, no automated color-semantics check | Compare rendered badge colors against the documented token palette in `05-DESIGN.md`; confirm each freshness state maps to a distinct, consistent color |
| `InventoryView`'s session-identity props documented at call site | SC-3 | Doc-presence check, no doc-linter configured | Confirm `App.js` has an inline comment/JSDoc referencing `05-DESIGN.md`, and `05-DESIGN.md` documents `householdId`/`userId`/`userName` |
| Every presentational component's data-only prop contract documented | SC-4 | Doc-presence check, no JSDoc-linter configured | Confirm a JSDoc block exists above each of the 6 components' function signatures, describing props with no internal fetch / no hard-coded fallback |
| Shared style-token set exists and is documented | SC-5 | Doc-presence + visual check, no tooling to automate | Confirm `:root` custom properties exist in `index.css` and are referenced/listed in `05-DESIGN.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies — **N/A for this phase**: all verification is manual per the table above (visual/doc-only success criteria, no REQ-IDs, no test framework in scope)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify — **N/A**, same reason
- [ ] Wave 0 covers all MISSING references — **N/A**, no Wave 0 gaps block this phase
- [ ] No watch-mode flags — N/A, no test commands
- [ ] Feedback latency < N/A s — N/A
- [ ] `nyquist_compliant: true` set in frontmatter — left `false`; this phase intentionally has no automated suite (documented, not a gap)

**Approval:** pending
