---
schema_version: 1
open_count: 4
waived_count: 0
fixed_count: 0
total_count: 4
last_updated: 2026-09-16T06:27:16.165Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | unrun-verify | .planning/phases/02-inventory-management/02-01-PLAN.md |  | Task 4's <human-check> browser click-through steps (start backend+frontend, manually restock Oats via the UI, confirm capacity/availability update without reload) were not run interactively; deferred to end-of-phase per HUMAN_VERIFY_MODE=end-of-phase. A live HTTP smoke test against the real Flask dev server (not just the Flask test client) was run as partial substitute evidence. | open |  | 2026-09-16T06:10:16.842Z |  |
| 2 | 02 | stub | client/src/App.js | 11 | HOUSEHOLD_ID/USER_ID are hardcoded placeholders (not fetched via a login/session flow) because Track A's auth/session layer (ACCT-04) has not landed yet; Track A wires real session values in once it lands. | open |  | 2026-09-16T06:10:22.438Z |  |
| 3 | 02 | unrun-verify | client/src/components/FreshnessBadge.js |  | Task 3 human-check (browser click-through confirming badge wording for Pantry/Fridge/Freezer at each freshness value) deferred per HUMAN_VERIFY_MODE=end-of-phase; automated checks (build, grep wording checks) passed. | open |  | 2026-09-16T06:19:14.794Z |  |
| 4 | 02 | unrun-verify | client/src/components/BatchList.js |  | Task 3 human-check (5-step browser click-through: merge Milk/milk batches with distinct best-by dates and confirm consumption order, loose-match merge (Whole Milk), ambiguous restock notice (Skim Milk then Milk), Freezer/Fridge location separation, no-best-by-date dash rendering) deferred per HUMAN_VERIFY_MODE=end-of-phase; automated checks (npm run build, no-sort grep, BatchList-wired grep, full pytest suite) all passed. | open |  | 2026-09-16T06:27:16.165Z |  |

````json
[
  {
    "id": 1,
    "kind": "unrun-verify",
    "phase": "02",
    "file": ".planning/phases/02-inventory-management/02-01-PLAN.md",
    "line": null,
    "description": "Task 4's <human-check> browser click-through steps (start backend+frontend, manually restock Oats via the UI, confirm capacity/availability update without reload) were not run interactively; deferred to end-of-phase per HUMAN_VERIFY_MODE=end-of-phase. A live HTTP smoke test against the real Flask dev server (not just the Flask test client) was run as partial substitute evidence.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-16T06:10:16.842Z",
    "resolved_at": null
  },
  {
    "id": 2,
    "kind": "stub",
    "phase": "02",
    "file": "client/src/App.js",
    "line": 11,
    "description": "HOUSEHOLD_ID/USER_ID are hardcoded placeholders (not fetched via a login/session flow) because Track A's auth/session layer (ACCT-04) has not landed yet; Track A wires real session values in once it lands.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-16T06:10:22.438Z",
    "resolved_at": null
  },
  {
    "id": 3,
    "kind": "unrun-verify",
    "phase": "02",
    "file": "client/src/components/FreshnessBadge.js",
    "line": null,
    "description": "Task 3 human-check (browser click-through confirming badge wording for Pantry/Fridge/Freezer at each freshness value) deferred per HUMAN_VERIFY_MODE=end-of-phase; automated checks (build, grep wording checks) passed.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-16T06:19:14.794Z",
    "resolved_at": null
  },
  {
    "id": 4,
    "kind": "unrun-verify",
    "phase": "02",
    "file": "client/src/components/BatchList.js",
    "line": null,
    "description": "Task 3 human-check (5-step browser click-through: merge Milk/milk batches with distinct best-by dates and confirm consumption order, loose-match merge (Whole Milk), ambiguous restock notice (Skim Milk then Milk), Freezer/Fridge location separation, no-best-by-date dash rendering) deferred per HUMAN_VERIFY_MODE=end-of-phase; automated checks (npm run build, no-sort grep, BatchList-wired grep, full pytest suite) all passed.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-16T06:27:16.165Z",
    "resolved_at": null
  }
]
````
