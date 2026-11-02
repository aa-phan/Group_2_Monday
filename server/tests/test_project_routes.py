"""HTTP-layer tests for the project routes (TD-05).

Ported from PR #7 onto the PR #9 routes. Real bugs the port exposed (B1-B5)
are strict xfails: they are recorded, not fixed, and not asserted as correct.
"""

import pytest

import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB
import usersDatabase as usersDB

PASSWORD = "correct horse battery"

B1 = pytest.mark.xfail(
    strict=True,
    raises=projectsDB.InvalidProjectInput,
    reason="B1: /get_user_projects_list does not catch InvalidProjectInput, so a non-string userId is an unhandled exception (HTTP 500)",
)
B2 = pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="B2: blank checks use `not value`, so a whitespace-only value passes validation and is persisted",
)
B3 = pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="B3: /create_project reports field 'creatorUserId', an internal parameter name, instead of the wire name 'userId'",
)
B4 = pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="B4: /join_project answers 404 project_not_found on projectId for a non-string userId, though the project exists and the bad field is userId",
)
B5 = pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="B5: create_project/join_project never check the Users collection, so a userId with no account becomes a project member",
)


@pytest.fixture
def carol(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)
    return "carol"


@pytest.fixture
def alice(mongo):
    usersDB.addUser(mongo, "Alice", "alice", PASSWORD)
    return "alice"


def _snapshot(mongo):
    db = mongo[hardwareDB.DB_NAME]
    return {
        name: sorted(
            (sorted((k, repr(v)) for k, v in doc.items() if k != "_id")
             for doc in db[name].find()),
        )
        for name in ("Users", hardwareDB.PROJECTS_COLLECTION)
    }


def _createBody(userId):
    return {
        "userId": userId, "projectId": "P9", "projectName": "Rover",
        "description": "desc",
    }


# ---------------------------------------------------------------------------
# POST /create_project
# ---------------------------------------------------------------------------


def test_create_project_returns_201_with_creator_as_member(api, carol):
    response = api.post("/create_project", json=_createBody(carol))

    assert response.status_code == 201
    assert response.get_json() == {"project": {
        "projectId": "P9", "projectName": "Rover", "description": "desc",
        "users": ["carol"],
    }}


def test_created_project_is_accepted_by_hardware_route(api, carol):
    api.post("/create_project", json=_createBody(carol))

    response = api.get("/api/hardware", query_string={
        "projectId": "P9", "userId": carol,
    })

    assert response.status_code == 200
    assert response.get_json()["hardwareSets"] == []


def test_create_project_requires_description(api, carol, mongo):
    before = _snapshot(mongo)
    body = _createBody(carol)
    del body["description"]

    response = api.post("/create_project", json=body)

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_input", "field": "description"}
    assert _snapshot(mongo) == before


@B5
def test_create_project_unknown_user(api, mongo):
    before = _snapshot(mongo)

    response = api.post("/create_project", json=_createBody("ghost"))

    assert response.status_code == 404
    assert response.get_json() == {"error": "user_not_found", "field": "userId"}
    assert _snapshot(mongo) == before


def test_create_project_duplicate_id(api, carol):
    body = _createBody(carol)
    api.post("/create_project", json=body)

    response = api.post("/create_project", json=body)

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "project_already_exists", "field": "projectId",
    }


def test_create_project_rejects_non_str_description(api, carol, mongo):
    before = _snapshot(mongo)
    body = _createBody(carol)
    body["description"] = 5

    response = api.post("/create_project", json=body)

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_input", "field": "description"}
    assert _snapshot(mongo) == before


# ---------------------------------------------------------------------------
# POST /join_project
# ---------------------------------------------------------------------------


def test_join_project_is_idempotent_and_grants_access(api, carol):
    body = {"userId": carol, "projectId": "H1"}

    first = api.post("/join_project", json=body)
    second = api.post("/join_project", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.get_json() == body

    info = api.post("/get_project_info", json={"projectId": "H1", "userId": carol})
    assert info.status_code == 200
    assert info.get_json()["project"]["users"].count("carol") == 1

    hardware = api.get("/api/hardware", query_string={
        "projectId": "H1", "userId": carol,
    })
    assert hardware.status_code == 200


@B5
def test_join_project_unknown_user(api, mongo):
    before = _snapshot(mongo)

    response = api.post("/join_project", json={"userId": "ghost", "projectId": "H1"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "user_not_found", "field": "userId"}
    assert _snapshot(mongo) == before


def test_join_project_unknown_project(api, carol):
    response = api.post("/join_project", json={"userId": carol, "projectId": "nope"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "project_not_found", "field": "projectId"}


# ---------------------------------------------------------------------------
# POST /get_user_projects_list
# ---------------------------------------------------------------------------


def test_get_user_projects_list(api, alice):
    response = api.post("/get_user_projects_list", json={"userId": alice})

    assert response.status_code == 200
    assert response.get_json() == {
        "projects": [{
            "projectId": "H1", "projectName": "", "description": "",
            "users": ["alice", "bob"],
        }],
    }


def test_get_user_projects_list_unknown_user_is_empty(api):
    response = api.post("/get_user_projects_list", json={"userId": "ghost"})

    assert response.status_code == 200
    assert response.get_json() == {"projects": []}


# ---------------------------------------------------------------------------
# POST /get_project_info
# ---------------------------------------------------------------------------


def test_project_info_for_member(api, alice):
    response = api.post("/get_project_info", json={"projectId": "H1", "userId": alice})

    assert response.status_code == 200
    assert response.get_json() == {"project": {
        "projectId": "H1", "projectName": "", "description": "",
        "users": ["alice", "bob"],
    }}


def test_project_info_same_403_for_non_member_and_missing_project(api, carol):
    nonMember = api.post("/get_project_info", json={"projectId": "H1", "userId": carol})
    missing = api.post("/get_project_info", json={"projectId": "nope", "userId": carol})

    assert nonMember.status_code == missing.status_code == 403
    assert nonMember.get_json() == missing.get_json() == {"error": "not_a_project_member"}


# ---------------------------------------------------------------------------
# Input validation across all POST routes
# ---------------------------------------------------------------------------

# Listed in each route's actual check order.
_REQUIRED = {
    "/create_project": ["projectName", "projectId", "description", "userId"],
    "/join_project": ["userId", "projectId"],
    "/get_project_info": ["projectId", "userId"],
    "/get_user_projects_list": ["userId"],
}

# A fully valid body per route, so one bad field is the only thing wrong.
_VALID = {
    "/create_project": _createBody("alice"),
    "/join_project": {"userId": "carol", "projectId": "H1"},
    "/get_project_info": {"userId": "alice", "projectId": "H1"},
    "/get_user_projects_list": {"userId": "alice"},
}


@pytest.mark.parametrize("route", sorted(_REQUIRED))
def test_empty_body_names_first_missing_field(api, route):
    response = api.post(route, json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_input", "field": _REQUIRED[route][0],
    }


_NON_STR = [{"$ne": ""}, 5, ["x"]]


def _caseA():
    cases = []

    def add(route, field, bad, *marks):
        cases.append(pytest.param(route, field, bad, marks=list(marks),
                                  id=f"{route}-{field}-{bad!r}"))

    for route, fields in sorted(_REQUIRED.items()):
        for field in fields:
            for bad in ("", None):
                add(route, field, bad)

    for field in ("projectName", "projectId", "description"):
        for bad in _NON_STR:
            add("/create_project", field, bad)
    for bad in _NON_STR:
        add("/create_project", "userId", bad, B3)
    for field in _REQUIRED["/create_project"]:
        add("/create_project", field, "   ", B2)
    add("/join_project", "userId", "   ", B2)
    for bad in _NON_STR:
        add("/join_project", "userId", bad, B4)
    for bad in _NON_STR:
        add("/get_user_projects_list", "userId", bad, B1)
    return cases


@pytest.mark.parametrize("route,field,bad", _caseA())
def test_bad_field_is_rejected_and_nothing_is_written(api, mongo, route, field, bad):
    usersDB.addUser(mongo, "Alice", "alice", PASSWORD)
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)
    body = dict(_VALID[route])
    body[field] = bad
    before = _snapshot(mongo)

    response = api.post(route, json=body)

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_input", "field": field}
    assert _snapshot(mongo) == before


# Group B: these bad values reach behavior main defines on purpose, so the
# real contract is asserted here instead of PR #7's blanket 400. Each
# response is truthful, writes nothing, and matches a docstring or an
# existing test. These are contracts, not accepted bugs.

_UNUSABLE = [{"$ne": ""}, 5, ["x"], "   "]


@pytest.mark.parametrize("bad", _UNUSABLE, ids=repr)
def test_join_project_unusable_project_id_is_project_not_found(api, carol, mongo, bad):
    before = _snapshot(mongo)

    response = api.post("/join_project", json={"userId": carol, "projectId": bad})

    assert response.status_code == 404
    assert response.get_json() == {"error": "project_not_found", "field": "projectId"}
    assert _snapshot(mongo) == before


@pytest.mark.parametrize("bad", _UNUSABLE, ids=repr)
@pytest.mark.parametrize("field", ["projectId", "userId"])
def test_project_info_unusable_id_is_not_a_member(api, alice, mongo, field, bad):
    before = _snapshot(mongo)
    body = {"projectId": "H1", "userId": alice}
    body[field] = bad

    response = api.post("/get_project_info", json=body)

    assert response.status_code == 403
    assert response.get_json() == {"error": "not_a_project_member"}
    assert _snapshot(mongo) == before


def test_user_projects_list_blank_user_id_is_an_empty_list(api):
    response = api.post("/get_user_projects_list", json={"userId": "   "})

    assert response.status_code == 200
    assert response.get_json() == {"projects": []}
