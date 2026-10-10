# Account & Authentication (Track A: US-01, US-02)

What Track A built on this branch: account sign-up, sign-in, and sign-out,
plus one small Track B fix (dynamic Check In/Check Out caps) made along
the way. This doc covers what changed and how to run/test it. For general
project setup (MongoDB/Flask/React, all three processes), see the main
[README.md](README.md) first -- this doc assumes that's already working.

## What's implemented

| Story | Status |
|---|---|
| US-01 Sign up | ✅ Done |
| US-02 Sign in | ✅ Done |
| Sign out | ✅ Done |
| TD-01 Encrypt credentials (bcrypt) | ✅ Done |
| TD-02 / ACCT-04 Session persistence | ❌ Not done -- a page refresh signs you out |
| US-03/04/05 Create/join/list projects | ❌ Not done -- see **Known limitation** below |

## How it works

**Backend** (`server/`):
- `passwordSecurity.py` -- `hashPassword`/`verifyPassword`, wrapping `bcrypt`. Each password gets its own random salt; hashing is one-way (no decrypt function exists by design).
- `usersDatabase.py` -- `addUser` hashes the password before storing it and rejects a taken `userId`; `login` verifies against the stored hash. A failed login returns the same result whether the `userId` doesn't exist or the password is wrong, on purpose -- this stops a login attempt from being used to find out which accounts exist.
- `app.py` -- `POST /add_user` and `POST /login` routes wire the above to HTTP (field validation -> 400, duplicate user -> 409, bad credentials -> 401, success -> 200/201).

**Frontend** (`client/src/`):
- `api/auth.js` -- `signUp`/`signIn` fetch wrappers, same shape as the existing `api/hardware.js`.
- `pages/MyRegistrationPage.js`, `pages/MyLoginPage.js` -- the actual forms, with inline validation, a busy/disabled submit state, and user-facing error messages.
- `App.js` -- replaces the old hardcoded demo user (`userId = 'alice'`) with real signed-in state. Shows sign-in/sign-up until an account exists, then renders the hardware view with the real `userId`, plus a **Sign out** link that clears that state. Signing out is a pure client-side reset -- there's no server-side session to invalidate yet (that's TD-02).

**Also touched (Track B's files, not Track A -- see note below):**
- `components/QuantityAction.js`, `CheckIn.js`, `CheckOut.js`, `HardwareSet.js` -- Check Out is now capped at units *available*; Check In is capped at units *checked out* (`capacity - available`), instead of an unbounded number. When there's nothing valid to do, the control disables outright.

## Known limitation: new accounts can't see hardware yet

Loading the hardware view requires your `userId` to already be a member of
the project (`projectsDatabase.py`'s `assertProjectMember`). Project
creation/joining (US-03/04/05) isn't built, so **a brand-new sign-up has no
way to become a project member** and will see a `not_a_project_member`
error after signing in. This isn't a bug in this work -- it's the next,
separate story.

To actually see data, sign in as the seeded demo user instead (see below),
or manually add a new `userId` to the seeded project's `users` array.

## Running it

Follow the main README's three processes (MongoDB, Flask, React), then
seed a demo account in addition to its existing hardware-set seed step:

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

(The main README's seed snippet already puts `'alice'` in the demo
project's `users` list -- run that too if you haven't.)

Open http://localhost:5173, sign in with:
- Username: `alice`
- User ID: `alice`
- Password: `correct horse battery`

## Testing it yourself

**Automated (fast, no servers needed):**

```bash
cd server && python -m pytest -v        # 139 tests
cd client && npm test                    # 66 tests
```

**Manually, via curl (useful for checking the API without a browser):**

```bash
curl -X POST http://localhost:5050/add_user -H "Content-Type: application/json" \
  -d '{"username":"bob","userId":"bob","password":"a real password"}'

curl -X POST http://localhost:5050/login -H "Content-Type: application/json" \
  -d '{"username":"bob","userId":"bob","password":"a real password"}'
```

**In the browser:** sign up, sign in, sign out, and try a wrong password --
see the **Known limitation** above before expecting a new sign-up to show
hardware data.

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

## A note on scope

`QuantityAction.js`/`CheckIn.js`/`CheckOut.js`/`HardwareSet.js` belong to
Track B (hardware resource management), not Track A. That fix was made at
the user's direct request while testing this branch -- worth flagging to
whoever owns Track B before merging, so it's not a surprise.
