---
phase: 261109-gee-demo-step-10-show-app-insufficient-stock
plan: 01
subsystem: client
tags: [react, checkout, validation, RES-04]
requires: []
provides:
  - Over-available Check Out reaches the server and shows the app's insufficient-stock alert
affects: [client/src/components/QuantityAction.js, client/src/components/CheckOut.js]
tech-stack:
  added: []
  patterns: [opt-out prop (capInput) for native input constraint]
key-files:
  created: [client/src/__tests__/checkout-over-available.test.js]
  modified:
    - client/src/components/QuantityAction.js
    - client/src/components/CheckOut.js
    - client/src/__tests__/components.test.js
decisions:
  - "Added optional capInput prop (default true) on QuantityAction rather than noValidate, so min/step checks and Check In stay unchanged"
metrics:
  tasks: 2
  commits: 3
completed: 2026-11-09
status: complete
commits: 3
plan_head_before: a53f13ddd4ff35eb367ae0912111b81e60fc71bd
plan_head_after: 28c63b3fbe49d49f0548594546a49fd92f90b1d1
actuals:
  tokens: 6000
  tasks: 2
  commits: 3
---

# Phase 261109-gee Plan 01: Over-available Check Out Summary

Check Out no longer puts `max={available}` on the native input (new `capInput={false}` prop on QuantityAction), so an over-available quantity is POSTed and the server's 409 renders as "Only N available -- can't check out M."

## Commits

- 6df0e5d test(261109-gee): failing end-to-end test (RED: no fetch, no alert)
- 70b3928 feat(261109-gee): capInput prop + CheckOut opt-out, updated max assertions
- 28c63b3 test(261109-gee): pin capInput contract (6 new unit tests)

## Results

- Client suite: 128 passed (121 baseline + 1 e2e + 6 unit); components.test.js 48 passed.
- `npm --prefix client run build` succeeded.
- CheckIn.js untouched; Check In max assertions unchanged.

## Deviations from Plan

None - plan executed as written (line numbers located by content after PR #14).

## Known Stubs

None.

## Self-Check: PASSED
