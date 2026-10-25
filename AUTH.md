# Account & Authentication (Track A: US-01, US-02, US-04)

What Track A built on this branch: account sign-up, sign-in, sign-out, and
joining the one seeded project so new accounts can actually use the app,
plus one small Track B fix (dynamic Check In/Check Out caps) made along
the way. This doc covers what changed and how to run/test it. For general
project setup (MongoDB/Flask/React, all three processes), see the main
[README.md](README.md) first -- this doc assumes that's already working.

## What's implemented

| Story | Status |
|---|---|
| US-01 Sign up | ✅ Done |
| US-02 Sign in | ✅ Done |
| US-04 Join a project | ✅ Done -- auto-joins the one seeded project on sign-in/up |
| Sign out | ✅ Done |
| TD-01 Encrypt credentials (bcrypt) | ✅ Done |
| TD-02 / ACCT-04 Session persistence | ❌ Not done -- a page refresh signs you out |
| US-03 Create a project | ❌ Not done -- there's only ever the one seeded project |
| US-05 View my projects | ❌ Not done -- same reason; nothing to list yet |

## How it works

**Backend** (`server/`):
- `passwordSecurity.py` -- `hashPassword`/`verifyPassword`, wrapping `bcrypt`. Each password gets its own random salt; hashing is one-way (no decrypt function exists by design).
- `usersDatabase.py` -- `addUser` hashes the password before storing it and rejects a taken `userId`; `login` verifies against the stored hash. A failed login returns the same result whether the `userId` doesn't exist or the password is wrong, on purpose -- this stops a login attempt from being used to find out which accounts exist. `joinProject` delegates to `projectsDatabase.addUser`.
- `projectsDatabase.py` -- `addUser(client, projectId, userId)` adds `userId` to a project's `users` list via `$addToSet` (joining twice is a no-op, not an error). Raises `ProjectNotFoundError` for an unknown `projectId`.
- `app.py` -- `POST /add_user`, `POST /login`, and `POST /join_project` routes wire the above to HTTP (field validation -> 400, duplicate user -> 409, bad credentials -> 401, unknown project -> 404, success -> 200/201).

**Frontend** (`client/src/`):
- `api/auth.js` -- `signUp`/`signIn` fetch wrappers, same shape as the existing `api/hardware.js`.
- `api/projects.js` -- `joinProject` fetch wrapper, same shape.
- `pages/MyRegistrationPage.js`, `pages/MyLoginPage.js` -- the actual forms, with inline validation, a busy/disabled submit state, and user-facing error messages.
- `App.js` -- replaces the old hardcoded demo user (`userId = 'alice'`) with real signed-in state. Shows sign-in/sign-up until an account exists; on success, calls `joinProject` against the one seeded project (`P1`) before rendering the hardware view with the real `userId`. Joining is idempotent server-side, so this runs on *every* sign-in too, not just sign-up -- which also self-heals any account created before this existed. A join failure is surfaced (non-fatal) rather than silently swallowed. A **Sign out** link clears all of this client-side state. Signing out is a pure client-side reset -- there's no server-side session to invalidate yet (that's TD-02).

**Also touched (Track B's files, not Track A -- see note below):**
- `components/QuantityAction.js`, `CheckIn.js`, `CheckOut.js`, `HardwareSet.js` -- Check Out is now capped at units *available*; Check In is capped at units *checked out* (`capacity - available`), instead of an unbounded number. When there's nothing valid to do, the control disables outright.

## There's only one project, and everyone joins it

There's no project creation or project list yet (US-03/US-05) -- the whole
app points at a single seeded project, `P1` (the `PROJECT_ID` constant in
`App.js`). What *is* done is that signing up or signing in automatically
joins you to it, so **any** account -- the seeded demo one or a brand-new
sign-up -- can see real hardware data right away. There's no dead end here
anymore; this used to be the known limitation, now fixed by US-04.

## Running it

Follow the main README's three processes (MongoDB, Flask, React), then
seed a demo account in addition to its existing hardware-set seed step
(this one's optional now -- any sign-up works -- but useful to have a
known-good account to demo with):

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
cd server && python -m pytest -v        # 150 tests
cd client && npm test                    # 72 tests
```

**Manually, via curl (useful for checking the API without a browser):**

```bash
curl -X POST http://localhost:5050/add_user -H "Content-Type: application/json" \
  -d '{"username":"bob","userId":"bob","password":"a real password"}'

curl -X POST http://localhost:5050/login -H "Content-Type: application/json" \
  -d '{"username":"bob","userId":"bob","password":"a real password"}'

curl -X POST http://localhost:5050/join_project -H "Content-Type: application/json" \
  -d '{"userId":"bob","projectId":"P1"}'
```

**In the browser:** sign up with any throwaway account, then straight into
the hardware view -- no detour, no error. Also try sign out and a wrong
password.

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

## A note on scope

`QuantityAction.js`/`CheckIn.js`/`CheckOut.js`/`HardwareSet.js` belong to
Track B (hardware resource management), not Track A. That fix was made at
the user's direct request while testing this branch -- worth flagging to
whoever owns Track B before merging, so it's not a surprise.
