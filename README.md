# AppDevProjectTemplate
Template for MIS385N (Advanced Programming and App Development) Team Project

[![CI](https://github.com/aa-phan/Group_2_Monday/actions/workflows/ci.yml/badge.svg)](https://github.com/aa-phan/Group_2_Monday/actions/workflows/ci.yml)

Every pull request runs the backend and client test suites, a client build, and a build and boot of the deploy image ([ci.yml](.github/workflows/ci.yml)). See [TESTING.md](TESTING.md) and [DEPLOY.md](DEPLOY.md).

# Running Locally

You need three processes: MongoDB, the Flask backend, and the React client. From the repo root:

```bash
# 1. MongoDB (leave running; port 27117)
mkdir -p server/.mongo-data
mongod --dbpath server/.mongo-data --port 27117 --bind_ip 127.0.0.1

# 2. Flask backend (new terminal; port 5050)
cd server
python3 -m venv venv && source venv/bin/activate   # first time only
pip install -r requirements.txt                      # first time only
MONGODB_URI="mongodb://127.0.0.1:27117/" python app.py

# 3. React client (new terminal; port 5173, proxies /api to 5050)
cd client
npm install                                          # first time only
npm run dev
```

Then open http://localhost:5173.

- **Configuration:** the server reads `MONGODB_URI` from the environment. Alternatively, put `MONGODB_URI=...` in `server/.env` (gitignored).
- **Seed data:** sign up (or sign in) in the browser, then from the project picker either create a new project or join an existing one by ID (see [AUTH.md](AUTH.md)). Hardware sets are a single **global** catalog shared by every project -- a project member can check in/out/request existing sets but cannot create new ones from the UI. To seed the catalog (one-time, before anyone can check anything out), run this from a Python shell with `MONGODB_URI` pointed at your database:
    ```bash
    cd server && source venv/bin/activate && python3 -c "
    from pymongo import MongoClient
    import hardwareDatabase as h
    c = MongoClient('mongodb://127.0.0.1:27117/')
    h.createHardwareSet(c, None, 'HWSet1', 10)
    h.createHardwareSet(c, None, 'HWSet2', 20)"
    ```
    Each set has a fixed capacity; Check Out and Check In only change availability, and it's the same capacity/availability no matter which project a member views it through. The projects collection is still named `Households` with a `householdId` field, left over from an earlier iteration of the project.
- **Port already in use:** check what is running with `lsof -i :27117 -i :5050 -i :5173`.
- **Tests:** `cd server && source venv/bin/activate && pytest`.

# Project Overview

A Flask + MongoDB + React app for managing shared hardware resources across
projects. Users sign up, create or join projects, and check hardware in/out
of a single catalog shared by every project.

The backend (`server/`) is split into four modules:

- `app.py` -- Flask routes for auth, projects, and hardware.
- `usersDatabase.py` -- accounts, password hashing (bcrypt), sessions.
- `projectsDatabase.py` -- creating/joining/listing projects.
- `hardwareDatabase.py` -- the global hardware catalog: checkout/checkin,
  rename, deactivate/reactivate, reservations.

For what's actually implemented, how each piece works, and the exact route
list, see:

- [AUTH.md](AUTH.md) -- accounts, sessions, and projects (Track A)
- [TESTING.md](TESTING.md) -- test suite layout and how to run it
- [DEPLOY.md](DEPLOY.md) -- hosting and environment variables
