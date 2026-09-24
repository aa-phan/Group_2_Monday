# Phase 5 (Track E): UI Design — Canonical Design Document

This document is the canonical reference for PantryTrack's shared design-token system and
`InventoryView`'s session-identity prop contract. **Track A** and **Track C** are its
readers: Track A wires real session values into `InventoryView`'s call site without
touching its internals, and Track C audits DATA-01/DATA-03 against the prop contracts
documented here and in each component's own JSDoc block. Any new UI work in Track A or
Track C should reference the same token names below rather than introducing new
color/spacing/typography/radius literals.

## Design Tokens

All tokens are CSS custom properties declared in a single `:root` block in
`client/src/index.css` and consumed via `var(--token-name)` from `client/src/App.css`
(and any future stylesheet). Track A and Track C adopt these by referencing the same
names rather than introducing new literals.

### Colour

| Token | Value | Purpose |
|-------|-------|---------|
| `--color-page` | `#F5F1E8` | Page background — warm parchment base |
| `--color-surface` | `#FCFAF5` | Card/panel surface — paper-like, distinct from page |
| `--color-ink` | `#2B2622` | Primary text colour |
| `--color-ink-muted` | `#6E655B` | Secondary/muted text (hints, notes, labels) |
| `--color-rule` | `#DDD5C7` | Default hairline border colour |
| `--color-rule-soft` | `#E7E0D3` | Softer hairline border (nested/inner dividers) |
| `--color-accent` | `#5C4433` | Deep pantry-shelf brown accent — hover/focus emphasis |
| `--color-danger` | `#8C2F22` | Error text colour |
| `--color-loc-pantry` | `#8A6A4B` | Pantry location stripe — shelf wood |
| `--color-loc-fridge` | `#5F8A7D` | Fridge location stripe — cool larder |
| `--color-loc-freezer` | `#5C7796` | Freezer location stripe — cold store |
| `--color-fresh-bg` | `#DCEFD8` | Freshness badge "fresh" background |
| `--color-fresh-fg` | `#2F5D2A` | Freshness badge "fresh" text |
| `--color-fresh-border` | `#A8CFA0` | Freshness badge "fresh" border |
| `--color-expiring-bg` | `#FAEBC8` | Freshness badge "expiring_soon" background |
| `--color-expiring-fg` | `#7A5310` | Freshness badge "expiring_soon" text |
| `--color-expiring-border` | `#E4C273` | Freshness badge "expiring_soon" border |
| `--color-expired-bg` | `#F7DFD8` | Freshness badge "expired" background |
| `--color-expired-fg` | `#8C2F22` | Freshness badge "expired" text |
| `--color-expired-border` | `#E0A99C` | Freshness badge "expired" border |
| `--color-unknown-bg` | `#EDE7DC` | Freshness badge "unknown" background |
| `--color-unknown-fg` | `#4A443C` | Freshness badge "unknown" text |
| `--color-unknown-border` | `#D4CBBC` | Freshness badge "unknown" border |
| `--color-claim-own-bg` | `#E4EBDF` | Reservation entry background — reserved by the current user |
| `--color-claim-own-fg` | `#3C5233` | Reservation entry text — reserved by the current user |
| `--color-claim-own-border` | `#B9C9AC` | Reservation entry border — reserved by the current user |
| `--color-claim-other-bg` | `#F2EDE2` | Reservation entry background — reserved by someone else |
| `--color-claim-other-fg` | `#6E655B` | Reservation entry text — reserved by someone else |
| `--color-claim-other-border` | `#E7E0D3` | Reservation entry border — reserved by someone else |

### Spacing

| Token | Value | Purpose |
|-------|-------|---------|
| `--space-3xs` | `2px` | Smallest gap — tight inline spacing |
| `--space-2xs` | `4px` | Compact gaps (labels, small notes) |
| `--space-xs` | `6px` | Small internal padding |
| `--space-sm` | `8px` | Default small padding/gap |
| `--space-md` | `10px` | Medium internal padding |
| `--space-lg` | `12px` | Larger internal padding (item-actions rows) |
| `--space-xl` | `16px` | Standard component padding/gap |
| `--space-2xl` | `24px` | Section spacing (indents, margins) |
| `--space-3xl` | `32px` | Large section spacing |
| `--space-4xl` | `64px` | Page-level bottom padding |

### Typography

| Token | Value | Purpose |
|-------|-------|---------|
| `--font-sans` | `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` | One humanist sans for both UI labels and data (D-07) |
| `--text-xs` | `0.8rem` | Smallest text (badges, fine print) |
| `--text-sm` | `0.85rem` | Small text (batch cards, notes) |
| `--text-md` | `0.9rem` | Medium text (item summary fields) |
| `--text-base` | `1rem` | Base body text size |
| `--weight-regular` | `400` | Regular font weight |
| `--weight-semibold` | `600` | Semibold font weight (names, badges) |
| `--leading-body` | `1.55` | Body line-height |

### Radius & structure

| Token | Value | Purpose |
|-------|-------|---------|
| `--radius-sm` | `4px` | Standard corner radius (cards, forms, buttons) |
| `--radius-pill` | `999px` | Pill shape (freshness badge) |
| `--rule-width` | `1px` | Standard hairline border width |
| `--stripe-width` | `4px` | Location-stripe left-border width on item cards |
| `--motion-fast` | `150ms` | Standard transition duration |
| `--ease-out` | `cubic-bezier(0.2, 0, 0, 1)` | Standard transition easing |

## InventoryView Session-Identity Contract

`InventoryView` (default export of `client/src/components/Project.js`) accepts three
session-identity props. It reads no global auth state and fetches only inventory data
(via `client/src/api/inventory.js`) — session identity must always be supplied by the
caller.

| Prop | Type | Used for |
|------|------|----------|
| `householdId` | `string` | The household whose inventory to load. Passed to `fetchInventory` and to every mutation call (`restock`, `consume`, `reserve`, `release`). |
| `userId` | `string` | The acting user's id. Used for reserve/consume/release calls and to distinguish "your own" reservations in the UI (`ItemActions`). |
| `userName` | `string` | Display name shown on reservation entries this user creates. |

None of these props has a default value or fallback. `InventoryView` does not read any
global auth/session state — the values must be supplied by its caller.

The current values in `client/src/App.js` (`HOUSEHOLD_ID = 'H1'`, `USER_ID = 'alice'`,
`USER_NAME = 'Alice'`) are development placeholders for this tracer slice only. Track A
replaces them with real session values sourced from its own auth/session layer once that
work lands, without editing `InventoryView` internals.

_Per-component prop contracts: added in plan 05-02._
