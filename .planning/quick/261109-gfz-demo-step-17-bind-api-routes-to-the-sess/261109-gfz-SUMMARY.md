---
phase: 261109-gfz-demo-step-17-bind-api-routes-to-the-sess
plan: 01
subsystem: auth
tags: [flask, session, authorization, react, vitest, pytest]
requires: []
provides:
  - requireSessionUser guard on all 11 project/hardware routes (401 not_signed_in, 403 forbidden_user_mismatch)
  - session username as /api/hardware/request requester
  - client returns to sign-in view on any 401 from hardware/project API
affects: [server/app.py, client/src/App.js]
tech-stack:
  added: []
  patterns: [route-table-driven authorization tests with url_map guard, publish-subscribe for API-to-App signalling]
key-files:
  created:
    - server/tests/test_session_authorization.py
    - client/src/api/sessionEvents.js
    - client/src/__tests__/session-expired.test.js
  modified:
    - server/app.py
    - server/tests/conftest.py
    - server/tests/test_api_contract.py
    - AUTH.md
    - client/src/App.js
    - client/src/api/hardware.js
    - client/src/api/projects.js
key-decisions:
  - "Session check runs after field checks and before getMongoClient(); the session userId (not the claimed one) reaches the DB layer"
  - "api test fixture signs in as the userId each request claims, copied as-is, so strict xfails B1-B5 stay at 17"
status: complete
metrics:
  duration: ~25m
  completed: 2026-11-09
estimate:
  tokens: 60000
actuals:
  tokens: 30000
  tasks: 3
  commits: 3
plan_head_before: 8e0c3db16399aaef89776c5c73b62c1c227c2e6d
plan_head_after: eef361441016f8380b8b91c9f62f0f269b9735d6
---

# Phase 261109-gfz Plan 01: Bind API routes to the session Summary

Every project and hardware route now requires a signed Flask session whose userId matches the one in the request (401 `not_signed_in` / 403 `forbidden_user_mismatch`), and the client returns to the sign-in view on any 401.

## Commits

- fdd5d71: Task 1 (tracer) - /join_project bound to session, signing test harness, route-table tests
- 6df59b6: Task 2 - remaining routes guarded, session username for /request, url_map guard test, AUTH.md
- eef3614: Task 3 - sessionEvents, 401 handling in hardware.js/projects.js, App.js sign-out on 401

## Results

- Server: 460 passed, 17 xfailed (baseline 404 passed, 17 xfailed)
- Client: 137 passed (baseline 128), production build succeeds
- server/hardwareDatabase.py, projectsDatabase.py, usersDatabase.py unchanged from 8e0c3db

## Deviations from Plan

None - plan executed as written. Note: in Task 2 the guard was applied before the new route rows were run, so the RED state for the nine unguarded routes was not observed separately; the 401/403 tests pass for all 11 rows and the url_map guard covers future routes.

The plan says "10 routes" but lists 11 (join_project plus ten more); all 11 are guarded and in the ROUTES table.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

All created files exist and commits fdd5d71, 6df59b6, eef3614 are on the branch.
