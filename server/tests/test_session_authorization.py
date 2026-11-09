"""Session authorization for the project/hardware routes (demo step 17).

Every project and hardware route used to trust the userId in the request
body/query. They now bind it to the signed session through
app.requireSessionUser: no session -> 401 not_signed_in, a session for a
different user -> 403 forbidden_user_mismatch. Order is field checks, then
the session check, then project membership.

ROUTES is the single table that drives every parametrized test below, and
test_every_route_is_in_the_table fails when a route is added to app.py
without a row here, so a future route cannot skip the session check.
"""

from dataclasses import dataclass
from typing import Callable

import pytest

import app as flask_app_module
import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB
import usersDatabase as usersDB

PASSWORD = "correct horse battery"

# Endpoints that are intentionally not session-bound (D-04).
EXEMPT_ENDPOINTS = {
    "login", "add_user", "me", "logout", "healthz", "serve_client", "static",
}


@dataclass
class Route:
    method: str
    path: str
    payload: Callable  # (ctx, userId) -> dict of fields claiming userId
    success: int
    missingError: str  # error code for the route's existing missing-field 400
    memberGated: bool


ROUTES = [
    Route(
        "POST", "/join_project",
        lambda ctx, uid: {"userId": uid, "projectId": "H1"},
        200, "invalid_input", False,
    ),
]


def _rowId(route):
    return f"{route.method} {route.path}"


@pytest.fixture
def seeded(mongo):
    """Users alice/bob exist (H1 already lists them); returns the context
    handed to the payload builders."""
    usersDB.addUser(mongo, "Alice", "alice", PASSWORD)
    usersDB.addUser(mongo, "Bob", "bob", PASSWORD)
    return {}


@pytest.fixture
def forbid_db(monkeypatch):
    """Replace getMongoClient with one that records the call and raises, so
    a test can prove the guard runs before any database connection."""
    calls = []

    def _boom():
        calls.append(1)
        raise AssertionError("getMongoClient called before the session check")

    monkeypatch.setattr(flask_app_module, "getMongoClient", _boom)
    return calls


def _snapshot(mongo):
    db = mongo[hardwareDB.DB_NAME]
    snap = {}
    for name in ("Users", hardwareDB.PROJECTS_COLLECTION,
                 hardwareDB.HARDWARE_SETS_COLLECTION):
        docs = [{k: v for k, v in d.items() if k != "_id"}
                for d in db[name].find()]
        snap[name] = sorted(docs, key=repr)
    return snap


def _call(client, route, payload):
    if route.method == "GET":
        return client.get(route.path, query_string=payload)
    return client.post(route.path, json=payload)


@pytest.mark.parametrize("route", ROUTES, ids=_rowId)
def test_no_session_is_401_and_touches_nothing(
    route, bare_api, mongo, seeded, forbid_db
):
    before = _snapshot(mongo)
    resp = _call(bare_api, route, route.payload(seeded, "alice"))
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "not_signed_in"}
    assert forbid_db == []
    assert _snapshot(mongo) == before


@pytest.mark.parametrize("route", ROUTES, ids=_rowId)
def test_other_users_session_is_403_and_touches_nothing(
    route, bare_api, mongo, seeded, sign_in, forbid_db
):
    sign_in(bare_api, "bob", "Bob")
    before = _snapshot(mongo)
    resp = _call(bare_api, route, route.payload(seeded, "alice"))
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "forbidden_user_mismatch"}
    assert forbid_db == []
    assert _snapshot(mongo) == before


@pytest.mark.parametrize("route", ROUTES, ids=_rowId)
def test_acting_as_yourself_succeeds(route, bare_api, seeded, sign_in):
    sign_in(bare_api, "alice", "Alice")
    resp = _call(bare_api, route, route.payload(seeded, "alice"))
    assert resp.status_code == route.success, resp.get_json()


@pytest.mark.parametrize("route", ROUTES, ids=_rowId)
def test_missing_userId_is_still_a_400_before_the_session_check(
    route, bare_api, seeded, forbid_db
):
    payload = route.payload(seeded, "alice")
    del payload["userId"]
    resp = _call(bare_api, route, payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == route.missingError
    assert forbid_db == []


# --- demo step 17, through the real /login cookie -------------------------


def test_demo_step_17_cannot_join_as_an_existing_member(bare_api, mongo, seeded):
    projectsDB.createProject(mongo, "Robotics", "P2", "desc", "bob")

    login = bare_api.post(
        "/login", json={"username": "Alice", "userId": "alice", "password": PASSWORD}
    )
    assert login.status_code == 200

    ok = bare_api.post("/join_project", json={"userId": "alice", "projectId": "P2"})
    assert ok.status_code == 200
    project = mongo[hardwareDB.DB_NAME][hardwareDB.PROJECTS_COLLECTION].find_one(
        {"householdId": "P2"}
    )
    assert "alice" in project["users"]

    spoof = bare_api.post("/join_project", json={"userId": "bob", "projectId": "P2"})
    assert spoof.status_code == 403
    assert spoof.get_json() == {"error": "forbidden_user_mismatch"}


def test_after_logout_the_same_call_is_401(bare_api, seeded):
    bare_api.post(
        "/login", json={"username": "Alice", "userId": "alice", "password": PASSWORD}
    )
    bare_api.post("/logout")
    resp = bare_api.post("/join_project", json={"userId": "alice", "projectId": "H1"})
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "not_signed_in"}
