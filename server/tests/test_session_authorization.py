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
    Route(
        "POST", "/get_user_projects_list",
        lambda ctx, uid: {"userId": uid},
        200, "invalid_input", False,
    ),
    Route(
        "POST", "/create_project",
        lambda ctx, uid: {
            "userId": uid, "projectId": "P9", "projectName": "Nine",
            "description": "desc",
        },
        201, "invalid_input", False,
    ),
    Route(
        "POST", "/get_project_info",
        lambda ctx, uid: {"userId": uid, "projectId": "H1"},
        200, "invalid_input", True,
    ),
    Route(
        "GET", "/api/hardware",
        lambda ctx, uid: {"userId": uid, "projectId": "H1"},
        200, "missing_parameter", True,
    ),
    Route(
        "POST", "/api/hardware/checkin",
        lambda ctx, uid: {
            "userId": uid, "projectId": "H1", "hwSetName": "HWSet1", "quantity": 1,
        },
        200, "invalid_input", True,
    ),
    Route(
        "POST", "/api/hardware/checkout",
        lambda ctx, uid: {
            "userId": uid, "projectId": "H1", "hwSetName": "HWSet1", "quantity": 1,
        },
        200, "invalid_input", True,
    ),
    Route(
        "POST", "/api/hardware/request",
        lambda ctx, uid: {
            "userId": uid, "projectId": "H1", "hwSetName": "HWSet1", "quantity": 1,
        },
        201, "invalid_input", True,
    ),
    Route(
        "POST", "/api/hardware/release",
        lambda ctx, uid: {
            "userId": uid, "projectId": "H1", "requestId": ctx["requestId"],
        },
        200, "invalid_input", True,
    ),
    Route(
        "POST", "/api/hardware/rename",
        lambda ctx, uid: {
            "userId": uid, "projectId": "H1", "hwSetName": "HWSet1",
            "newName": "HWSetRenamed",
        },
        200, "invalid_input", True,
    ),
    Route(
        "POST", "/api/hardware/set_active",
        lambda ctx, uid: {
            "userId": uid, "projectId": "H1", "hwSetName": "HWSet1", "active": True,
        },
        200, "invalid_input", True,
    ),
]


def _rowId(route):
    return f"{route.method} {route.path}"


@pytest.fixture
def seeded(mongo):
    """Users alice/bob exist (H1 already lists them), HWSet1 in H1 has units
    checked out and one request; returns the context handed to the payload
    builders (the seeded requestId)."""
    usersDB.addUser(mongo, "Alice", "alice", PASSWORD)
    usersDB.addUser(mongo, "Bob", "bob", PASSWORD)
    hardwareDB.createHardwareSet(mongo, "H1", "HWSet1", 10)
    hardwareDB.checkoutHardware(mongo, "H1", "HWSet1", 3, "alice")
    reservationId, _ = hardwareDB.addReservation(
        mongo, "H1", "HWSet1", 1, "alice", "Alice"
    )
    return {"requestId": reservationId}


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


MEMBER_GATED = [r for r in ROUTES if r.memberGated]


@pytest.mark.parametrize("route", MEMBER_GATED, ids=_rowId)
def test_signed_in_non_member_is_403_not_a_project_member(
    route, bare_api, mongo, seeded, sign_in
):
    sign_in(bare_api, "mallory", "Mallory")
    before = _snapshot(mongo)
    resp = _call(bare_api, route, route.payload(seeded, "mallory"))
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "not_a_project_member"}
    assert _snapshot(mongo) == before


def test_request_records_the_session_username_not_the_body_userName(
    bare_api, mongo, seeded, sign_in
):
    sign_in(bare_api, "alice", "Alice")
    resp = bare_api.post(
        "/api/hardware/request",
        json={
            "userId": "alice", "userName": "Mallory", "projectId": "H1",
            "hwSetName": "HWSet1", "quantity": 1,
        },
    )
    assert resp.status_code == 201
    raw = mongo[hardwareDB.DB_NAME][hardwareDB.HARDWARE_SETS_COLLECTION].find_one(
        {"hwSetName": "HWSet1"}
    )
    reservation = [
        r for r in raw["reservations"] if r["reservationId"] == resp.get_json()["requestId"]
    ][0]
    assert reservation["userName"] == "Alice"
    assert "Mallory" not in repr(raw["reservations"])


def test_every_route_is_in_the_table():
    actual = set()
    for rule in flask_app_module.app.url_map.iter_rules():
        if rule.endpoint in EXEMPT_ENDPOINTS:
            continue
        for method in rule.methods & {"GET", "POST"}:
            actual.add((method, rule.rule))
    listed = {(r.method, r.path) for r in ROUTES}
    assert actual == listed, (
        "Routes in app.py and ROUTES differ (unlisted: "
        f"{sorted(actual - listed)}, stale: {sorted(listed - actual)}). Add a "
        "ROUTES row, which brings the route under the 401/403 coverage, or "
        "justify an EXEMPT_ENDPOINTS entry."
    )


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
