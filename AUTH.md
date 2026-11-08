# Account & Authentication (Track A: US-01 through US-05, TD-02)

What Track A built: account sign-up, sign-in, sign-out, a real persisted
session that survives a page refresh (and even a backend restart),
creating a project, joining an existing project by ID, and viewing/
switching between every project a user belongs to -- plus one small
Track B fix (dynamic Check In/Check Out caps) made along the way. This
doc covers what changed and how to run/test it. For general project
setup (MongoDB/Flask/React, all three processes), see the main
[README.md](README.md) first -- this doc assumes that's already working.

## What's implemented

| Story | Status |
|---|---|
| US-01 Sign up | ✅ Done |
| US-02 Sign in | ✅ Done |
| US-03 Create a project | ✅ Done -- creator is added as the first member |
| US-04 Join a project | ✅ Done -- join any project by ID from the project picker |
| US-05 View my projects | ✅ Done -- project picker lists every project the user belongs to |
| Sign out | ✅ Done |
| TD-01 Encrypt credentials (bcrypt) | ✅ Done |
| TD-02 / ACCT-04 Session persistence | ✅ Done -- survives a refresh and a backend restart |

## How it works

**Backend** (`server/`):
- `passwordSecurity.py` -- `hashPassword`/`verifyPassword`, wrapping `bcrypt`. Each password gets its own random salt; hashing is one-way (no decrypt function exists by design).
- `usersDatabase.py` -- `addUser` hashes the password before storing it and rejects a taken `userId`; `login` verifies against the stored hash. A failed login returns the same result whether the `userId` doesn't exist or the password is wrong, on purpose -- this stops a login attempt from being used to find out which accounts exist. `joinProject` delegates to `projectsDatabase.addUser`; `getUserProjectsList` delegates to `projectsDatabase.getUserProjects`.
- `projectsDatabase.py`:
  - `addUser(client, projectId, userId)` adds `userId` to a project's `users` list via `$addToSet` (joining twice is a no-op, not an error). Raises `ProjectNotFoundError` for an unknown `projectId`.
  - `createProject(client, projectName, projectId, description, creatorUserId)` (US-03) inserts a new project document with `creatorUserId` as its first member. A unique index on the stored `householdId` field (mirroring `hardwareDatabase.py`'s own unique-index pattern) makes this race-safe: two concurrent creates for the same `projectId` can't both succeed. Raises `ProjectAlreadyExistsError` (409) if `projectId` is taken, or `InvalidProjectInput` (400) if any field is missing or not a string.
  - `queryProject(client, projectId)` returns one project's info (name/description/members) or `None`.
  - `getUserProjects(client, userId)` (US-05) returns every project whose `users` list contains `userId`, sorted by `projectId`. The project's own `users` array stays the single source of truth for membership -- there's no separate `projects` list kept on the user document to go stale.
- `app.py` -- `POST /add_user`, `POST /login`, `POST /join_project`, `POST /create_project`, `POST /get_user_projects_list`, `POST /get_project_info`, `GET /me`, and `POST /logout` routes wire the above to HTTP (field validation -> 400, duplicate user/project -> 409, bad credentials -> 401, non-member -> 403, success -> 200/201). `app.secret_key` signs the session cookie Flask's built-in `session` uses -- read from `SECRET_KEY` in `server/.env` (same place as `MONGODB_URI`) so it's stable across restarts; falls back to a random per-process key (with a printed warning) if unset, which still works but won't survive a restart.

**Frontend** (`client/src/`):
- `api/auth.js` -- `signUp`/`signIn` fetch wrappers, same shape as the existing `api/hardware.js`. Plus `getCurrentSession` (`GET /me`) and `signOut` (`POST /logout`) for TD-02.
- `api/projects.js` -- `joinProject`, `createProject`, `getUserProjects`, `getProjectInfo` fetch wrappers, same shape.
- `pages/MyRegistrationPage.js`, `pages/MyLoginPage.js` -- the actual sign-up/sign-in forms, with inline validation, a busy/disabled submit state, and user-facing error messages.
- `pages/MyProjectsPage.js` (US-03/US-05, new) -- on mount, fetches every project the signed-in user belongs to and lists it with an "Open" button. Also has a "Create a project" form (ID/name/description) and a "Join a project" form (ID only); both land on the newly created/joined project immediately on success.
- `App.js` -- replaces the old hardcoded demo user (`userId = 'alice'`) and single hardcoded project (`PROJECT_ID = 'P1'`) with real signed-in state plus a `selectedProjectId` that starts at `null`. On mount, calls `getCurrentSession` (briefly showing "Checking session..."); if a valid session cookie exists, restores the signed-in view with no sign-in prompt at all. Otherwise shows sign-in/sign-up; on success, renders `MyProjectsPage` (the project picker) rather than any one project. Picking "Open" on a project (or creating/joining one) sets `selectedProjectId`, which renders the hardware resource view for that project with a "Back to my projects" control. **Sign out** calls `signOut` (clearing the session server-side, not just local state), clears the local view, and resets `selectedProjectId` back to the picker regardless of whether the call succeeds.

**Also touched (Track B's files, not Track A -- see note below):**
- `components/QuantityAction.js`, `CheckIn.js`, `CheckOut.js`, `HardwareSet.js` -- Check Out is now capped at units *available*; Check In is capped at units *checked out* (`capacity - available`), instead of an unbounded number. When there's nothing valid to do, the control disables outright.

## How the session actually works (and what it doesn't cover)

This is Flask's built-in session, not a hand-rolled token or `localStorage`:
on sign-in/up, the server sets `session['userId']`/`session['username']`,
which Flask turns into a cryptographically **signed, httpOnly** cookie.
Signed means the client can't forge or edit it (no `SECRET_KEY`, no valid
cookie); httpOnly means client-side JS -- including an XSS payload --
can't even read it. `GET /me` reads it back; `POST /logout` clears it
server-side, so a stale copy of the cookie stops working immediately.

**What this does *not* cover:** every other route (`/api/hardware/*`)
still takes `userId` as a plain value in the request body/query string and
trusts it, with zero session check. So this makes *login state* tamper-
resistant, but doesn't yet stop someone who already knows a `userId` from
calling those other routes "as" them without a password -- that would mean
requiring a valid session on every route, not just restoring one across a
refresh. That's a further hardening step, not part of TD-02 itself.

## Projects are now created, joined, and listed for real

US-03/US-05 removed the old single-seeded-project assumption. After
signing in, a user lands on a project picker (not a hardcoded project):
they can open any project they already belong to, create a brand-new one
(becoming its first member automatically), or join an existing one by
ID. The previously-seeded demo project (`P1` in earlier test data) still
works exactly the same way -- it's just an ordinary project now, joined
like any other via `POST /join_project` instead of automatically on
every sign-in.

## Running it

Follow the main README's three processes (MongoDB, Flask, React). Also
set a stable `SECRET_KEY` in `server/.env` (alongside `MONGODB_URI`) so
sessions survive a backend restart, not just a refresh -- without it,
the app still works, but everyone gets signed out whenever Flask restarts:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"  # paste the output as SECRET_KEY=... in server/.env
```

Then seed a demo account in addition to its existing hardware-set seed
step (this one's optional now -- any sign-up works -- but useful to have
a known-good account to demo with):

```bash
cd server
python3 -c "
from pymongo import MongoClient
import hardwareDatabase as h
import usersDatabase as u
c = MongoClient('mongodb://127.0.0.1:27117/')  # match your MONGODB_URI
u.addUser(c, 'alice', 'alice', 'correct horse battery')
"
```

Open http://localhost:5173 and either sign in with:
- Username: `alice`
- User ID: `alice`
- Password: `correct horse battery`

...or just sign up with any new username/userId/password -- it'll work
end to end on the first try.

## Testing it yourself

**Automated (fast, no servers needed):**

```bash
cd server && python -m pytest -v        # 330 tests
cd client && npm test                    # 121 tests
```

**Manually, via curl (useful for checking the API without a browser --
note `-c`/`-b` to actually carry the session cookie like a browser would):**

```bash
curl -c cookies.txt -X POST http://localhost:5050/login -H "Content-Type: application/json" \
  -d '{"username":"alice","userId":"alice","password":"correct horse battery"}'

curl -b cookies.txt http://localhost:5050/me   # same identity back, no credentials needed

curl -b cookies.txt -c cookies.txt -X POST http://localhost:5050/logout

curl -b cookies.txt http://localhost:5050/me   # now 401 -- the session is gone
```

**In the browser:** sign up with any throwaway account, then straight into
the hardware view -- no detour, no error. Refresh the page (stays signed
in), sign out (returns to the sign-in form, even after a refresh), and try
a wrong password.

## API reference

### `POST /add_user`
```json
// Request
{ "username": "alice", "userId": "alice", "password": "correct horse battery" }

// 201 success
{ "username": "alice", "userId": "alice" }

// 400 -- missing field
{ "error": "invalid_input", "field": "password" }

// 409 -- userId taken
{ "error": "user_already_exists", "field": "userId" }
```
Password must be 8-72 characters (bcrypt only uses the first 72 bytes of
any input, so longer passwords are rejected rather than silently truncated).

### `POST /login`
```json
// Request
{ "username": "alice", "userId": "alice", "password": "correct horse battery" }

// 200 success
{ "username": "alice", "userId": "alice" }

// 401 -- wrong password OR unknown user (deliberately the same response)
{ "error": "invalid_credentials" }
```

### `POST /join_project`
```json
// Request
{ "userId": "alice", "projectId": "P1" }

// 200 success (also returned if already a member -- idempotent)
{ "userId": "alice", "projectId": "P1" }

// 400 -- missing field
{ "error": "invalid_input", "field": "projectId" }

// 404 -- projectId doesn't match any existing project
{ "error": "project_not_found", "field": "projectId" }
```

### `POST /create_project` (US-03)
```json
// Request
{ "projectId": "P2", "projectName": "Robotics Club", "description": "Shared lab hardware", "userId": "alice" }

// 201 success -- userId becomes the project's first member
{ "project": { "projectId": "P2", "projectName": "Robotics Club", "description": "Shared lab hardware", "users": ["alice"] } }

// 400 -- missing/empty field
{ "error": "invalid_input", "field": "projectName" }

// 409 -- projectId already taken
{ "error": "project_already_exists", "field": "projectId" }
```

### `POST /get_user_projects_list` (US-05)
```json
// Request
{ "userId": "alice" }

// 200 success -- every project alice belongs to, sorted by projectId
{ "projects": [ { "projectId": "P1", "projectName": "...", "description": "...", "users": ["alice", "bob"] } ] }

// 400 -- missing field
{ "error": "invalid_input", "field": "userId" }
```

### `POST /get_project_info`
```json
// Request
{ "projectId": "P1", "userId": "alice" }

// 200 success
{ "project": { "projectId": "P1", "projectName": "...", "description": "...", "users": [...] } }

// 403 -- userId is not a member of projectId (also returned for an unknown projectId,
// so a non-member can't use this to discover which project IDs exist)
{ "error": "not_a_project_member" }
```

### `GET /me`
```json
// 200 -- a valid session cookie was sent
{ "username": "alice", "userId": "alice" }

// 401 -- no session, or it was cleared by /logout
{ "error": "not_signed_in" }
```

### `POST /logout`
```json
// 200 -- always, whether or not there was a session to clear
{}
```

## A note on scope

`QuantityAction.js`/`CheckIn.js`/`CheckOut.js`/`HardwareSet.js`/
`MyCheckedOut.js` and `hardwareDatabase.py`/`projectsDatabase.py` belong
to Track B (hardware resource management), not Track A. The changes below
were made at the user's direct request while testing this branch:

1. Capping Check In/Check Out at real numbers instead of an unbounded field.
2. **Per-(user, project) checkout accountability** -- found while testing:
   any project member could check in units a *different* member checked
   out, because `checkedOut` was only ever a project-wide aggregate with
   no record of who personally held what. `hardwareDatabase.py` tracks a
   `checkedOutBy` ledger (array of `{userId, projectId, quantity}`, one
   entry per (userId, projectId) pair) alongside the existing aggregate;
   checkout still draws from the shared global pool, but checkin is gated
   by what the calling user personally holds *through the same project
   they're acting through*. Originally this ledger was keyed by userId
   alone; once hardware became a global catalog (see item 3) that let the
   same user check in through ANY project they belonged to, regardless of
   which project they actually checked out through -- found while testing
   that change, and fixed by adding projectId to the ledger key. The API
   returns `myCheckedOut` on each hardware set (the asking user's own
   holding through the project they're currently viewing), and the UI
   shows it as a "You've Checked Out" cell. See `hardwareDatabase.py`'s
   module docstring and `server/tests/test_per_user_checkout.py` for the
   full reasoning and coverage of both bugs' before/after.
3. **Hardware sets are a single global catalog, not per-project** --
   course-staff feedback: a project must not be able to mint its own
   private hardware. A brief earlier version of this branch added
   `POST /api/hardware/create` plus a frontend form so a project member
   could give "their" project a first hardware set; both are now removed.
   `hardwareDatabase.py`'s collection is keyed by `hwSetKey` alone (a
   single unique index, not a `(projectId, hwSetKey)` compound one), and
   `getHardwareStatus` returns every set in the catalog regardless of
   which project's member is asking -- every project's members see and
   draw from the exact same stock. `projectId` is still required on every
   hardware route and still gates membership (`assertProjectMember`) the
   same as before; it just no longer partitions *which hardware* exists.
   `createHardwareSet` still exists in `hardwareDatabase.py` for one-time
   seeding (see the main README's "Seed data" section) but is not
   reachable from any route. See `hardwareDatabase.py`'s module docstring
   and `server/tests/test_adversarial_hardware.py`'s
   `test_status_lists_the_entire_global_catalog_regardless_of_which_project_asks`
   / `test_release_works_through_any_project_the_releaser_belongs_to` for
   the behavior this pins down.

This is a real change to Track B's data model and logic, not cosmetic --
worth a direct conversation with whoever owns Track B before merging, not
just a note in this doc.
