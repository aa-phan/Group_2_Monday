---
status: testing
phase: 02-inventory-management
source: [02-VERIFICATION.md]
started: 2026-09-16T02:00:00Z
updated: 2026-09-16T02:00:00Z
---

## Current Test

number: 1
name: Restock tracer browser click-through
expected: |
  Restock "Oats" 4 units into Pantry via the running UI — item appears with capacity 4/availability 4
  with no page reload. Restock 3 more units of "Oats" — confirm it merges into ONE Oats row showing
  capacity 7, not two separate rows.
awaiting: user response

## Tests

### 1. Restock tracer browser click-through
expected: Item appears live after submit with no reload; second restock merges into the same row (capacity 7).
result: [pending]

### 2. Freshness badge wording browser click-through
expected: |
  Restock 4 items across Pantry/Fridge/Freezer with dates chosen to land in each freshness band.
  Badge wording: Pantry/Fridge use "Fresh"/"Use soon"/"Past best-by"; Freezer uses "Good quality"/
  "Quality declining"/"Freezer burn risk" (no safety/discard language); a batch with no date shows "No date".
result: [pending]

### 3. Batch matching and detail browser click-through
expected: |
  Merge "Milk"/"milk" batches with distinct best-by dates, confirm consumption order on expand.
  Loose-match "Whole Milk" into "Milk". Trigger an ambiguous restock ("Skim Milk" + "Milk" both present,
  then restock "Milk") and confirm the ambiguity notice names both colliding items. Confirm Fridge/Freezer
  location separation. Confirm a batch with no best-by date renders a dash.
result: [pending]

### 4. Consume/reserve/release browser click-through
expected: |
  Consume drains the soonest-expiring batch first. An over-consume shows the on-hand count and keeps
  the typed quantity. Reserving shows the claimant's name and drops availability. Another member's
  consume still succeeds on a fully-reserved item (reserve is dibs, not a lock). The release button is
  hidden for non-owners and works for the owner. Two reservations by the same member are each
  independently releasable.
result: [pending]

### 5. Concurrent-consume race
expected: |
  Run two genuinely concurrent consume requests against a real multi-threaded MongoDB (not mongomock)
  that together exceed capacity. Exactly one succeeds; the other gets 409; capacity never goes negative.
  (This is a backstop-verified truth — no executed race test exists yet since mongomock is single-threaded.)
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
