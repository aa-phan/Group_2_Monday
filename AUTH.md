# Account & Authentication (Track A: US-01, US-02, US-04, TD-02)

What Track A built on this branch: account sign-up, sign-in, sign-out,
joining the one seeded project so new accounts can actually use the app,
and a real persisted session that survives a page refresh (and even a
backend restart) -- plus one small Track B fix (dynamic Check In/Check
Out caps) made along the way. This doc covers what changed and how to
run/test it. For general project setup (MongoDB/Flask/React, all three
processes), see the main [README.md](README.md) first -- this doc
assumes that's already working.

## What's implemented

| Story | Status |
|---|---|
| US-01 Sign up | ✅ Done |
| US-02 Sign in | ✅ Done |
| US-04 Join a project | ✅ Done -- auto-joins the one seeded project on sign-in/up |
| Sign out | ✅ Done |
| TD-01 Encrypt credentials (bcrypt) | ✅ Done |
| TD-02 / ACCT-04 Session persistence | ✅ Done -- survives a refresh and a backend restart |
| US-03 Create a project | ❌ Not done -- there's only ever the one seeded project |
| US-05 View my projects | ❌ Not done -- same reason; nothing to list yet |

## How it works

**Backend** (`server/`):
- `passwordSecurity.py` -- `hashPassword`/`verifyPassword`, wrapping `bcrypt`. Each password gets its own random salt; hashing is one-way (no decrypt function exists by design).
- `usersDatabase.py` -- `addUser` hashes the password before storing it and rejects a taken `userId`; `login` verifies against the stored hash. A failed login returns the same result whether the `userId` doesn't exist or the password is wrong, on purpose -- this stops a login attempt from being used to find out which accounts exist. `joinProject` delegates to `projectsDatabase.addUser`.
- `projectsDatabase.py` -- `addUser(client, projectId, userId)` adds `userId` to a project's `users` list via `$addToSet` (joining twice is a no-op, not an error). Raises `ProjectNotFoundError` for an unknown `projectId`.
- `app.py` -- `POST /add_user`, `POST /login`, `POST /join_project`, `GET /me`, and `POST /logout` routes wire the above to HTTP (field validation -> 400, duplicate user -> 409, bad credentials -> 401, unknown project -> 404, success -> 200/201). `app.secret_key` signs the session cookie Flask's built-in `session` uses -- read from `SECRET_KEY` in `server/.env` (same place as `MONGODB_URI`) so it's stable across restarts; falls back to a random per-process key (with a printed warning) if unset, which still works but won't survive a restart.

**Frontend** (`client/src/`):
- `api/auth.js` -- `signUp`/`signIn` fetch wrappers, same shape as the existing `api/hardware.js`. Plus `getCurrentSession` (`GET /me`) and `signOut` (`POST /logout`) for TD-02.
- `api/projects.js` -- `joinProject` fetch wrapper, same shape.
- `pages/MyRegistrationPage.js`, `pages/MyLoginPage.js` -- the actual forms, with inline validation, a busy/disabled submit state, and user-facing error messages.
- `App.js` -- replaces the old hardcoded demo user (`userId = 'alice'`) with real signed-in state. On mount, calls `getCurrentSession` (briefly showing "Checking session..."); if a valid session cookie exists, restores the signed-in view with no sign-in prompt at all. Otherwise shows sign-in/sign-up; on success, calls `joinProject` against the one seeded project (`P1`) before rendering the hardware view with the real `userId`. Joining is idempotent server-side, so this runs on *every* sign-in too, not just sign-up -- which also self-heals any account created before this existed. A join failure is surfaced (non-fatal) rather than silently swallowed. **Sign out** calls `signOut` (clearing the session server-side, not just local state) and clears the local view regardless of whether that call succeeds.

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

## There's only one project, and everyone joins it

There's no project creation or project list yet (US-03/US-05) -- the whole
app points at a single seeded project, `P1` (the `PROJECT_ID` constant in
`App.js`). What *is* done is that signing up or signing in automatically
joins you to it, so **any** account -- the seeded demo one or a brand-new
sign-up -- can see real hardware data right away. There's no dead end here
anymore; this used to be the known limitation, now fixed by US-04.

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
cd server && python -m pytest -v        # 156 tests
cd client && npm test                    # 84 tests
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

`QuantityAction.js`/`CheckIn.js`/`CheckOut.js`/`HardwareSet.js` belong to
Track B (hardware resource management), not Track A. That fix was made at
the user's direct request while testing this branch -- worth flagging to
whoever owns Track B before merging, so it's not a surprise.
