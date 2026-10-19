"""HTTP-layer tests for the project routes (TD-05)."""

import pytest

import hardwareDatabase as hardwareDB
import usersDatabase as usersDB

PASSWORD = "correct horse battery"


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


# ---------------------------------------------------------------------------
# POST /create_project
# ---------------------------------------------------------------------------


def test_create_project_returns_201_with_creator_as_member(api, carol):
    response = api.post("/create_project", json={
        "userId": carol, "projectId": "P9", "projectName": "Rover",
        "description": "desc",
    })

    assert response.status_code == 201
    assert response.get_json() == {"project": {
        "projectId": "P9", "projectName": "Rover", "description": "desc",
        "users": ["carol"],
    }}


def test_created_project_is_accepted_by_hardware_route(api, carol):
    api.post("/create_project", json={
        "userId": carol, "projectId": "P9", "projectName": "Rover",
    })

    response = api.get("/api/hardware", query_string={
        "projectId": "P9", "userId": carol,
    })

    assert response.status_code == 200
    assert response.get_json()["hardwareSets"] == []


def test_create_project_description_defaults_to_empty(api, carol):
    response = api.post("/create_project", json={
        "userId": carol, "projectId": "P9", "projectName": "Rover",
    })

    assert response.get_json()["project"]["description"] == ""


def test_create_project_unknown_user(api):
    response = api.post("/create_project", json={
        "userId": "ghost", "projectId": "P9", "projectName": "Rover",
    })

    assert response.status_code == 404
    assert response.get_json() == {"error": "user_not_found", "field": "userId"}


def test_create_project_duplicate_id(api, carol):
    body = {"userId": carol, "projectId": "P9", "projectName": "Rover"}
    api.post("/create_project", json=body)

    response = api.post("/create_project", json=body)

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "project_already_exists", "field": "projectId",
    }


def test_create_project_rejects_non_str_description(api, carol, mongo):
    before = _snapshot(mongo)

    response = api.post("/create_project", json={
        "userId": carol, "projectId": "P9", "projectName": "Rover",
        "description": 5,
    })

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
    users = second.get_json()["project"]["users"]
    assert users.count("carol") == 1

    hardware = api.get("/api/hardware", query_string={
        "projectId": "H1", "userId": carol,
    })
    assert hardware.status_code == 200


def test_join_project_unknown_user(api):
    response = api.post("/join_project", json={"userId": "ghost", "projectId": "H1"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "user_not_found", "field": "userId"}


def test_join_project_unknown_project(api, carol):
    response = api.post("/join_project", json={"userId": carol, "projectId": "nope"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "project_not_found", "field": "projectId"}


# ---------------------------------------------------------------------------
# POST /get_user_projects_list and GET /main
# ---------------------------------------------------------------------------


def test_get_user_projects_list(api, alice):
    response = api.post("/get_user_projects_list", json={"userId": alice})

    assert response.status_code == 200
    assert response.get_json() == {
        "userId": "alice",
        "projects": [{"projectId": "H1", "projectName": "", "description": ""}],
    }


def test_get_user_projects_list_unknown_user(api):
    response = api.post("/get_user_projects_list", json={"userId": "ghost"})

    assert response.status_code == 404
    assert response.get_json()["error"] == "user_not_found"


def test_main_returns_portal_summary_without_password(api, alice):
    response = api.get("/main", query_string={"userId": alice})

    assert response.status_code == 200
    body = response.get_json()
    assert body == {
        "username": "Alice",
        "userId": "alice",
        "projects": [{"projectId": "H1", "projectName": "", "description": ""}],
    }
    assert "password" not in response.get_data(as_text=True)


def test_main_reflects_live_data(api, carol):
    api.post("/create_project", json={
        "userId": carol, "projectId": "P9", "projectName": "Rover",
    })

    projects = api.get("/main", query_string={"userId": carol}).get_json()["projects"]

    assert [p["projectId"] for p in projects] == ["P9"]


def test_main_missing_user_id(api):
    response = api.get("/main")

    assert response.status_code == 400
    assert response.get_json() == {"error": "missing_parameter", "field": "userId"}


def test_main_unknown_user(api):
    response = api.get("/main", query_string={"userId": "ghost"})

    assert response.status_code == 404
    assert response.get_json()["error"] == "user_not_found"


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

_REQUIRED = {
    "/create_project": ["userId", "projectId", "projectName"],
    "/join_project": ["userId", "projectId"],
    "/get_project_info": ["userId", "projectId"],
    "/get_user_projects_list": ["userId"],
}


@pytest.mark.parametrize("route", sorted(_REQUIRED))
def test_empty_body_names_first_missing_field(api, route):
    response = api.post(route, json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_input", "field": _REQUIRED[route][0],
    }


_BAD_VALUES = [{"$ne": ""}, 5, "", "   ", None, ["x"]]


@pytest.mark.parametrize("bad", _BAD_VALUES, ids=repr)
@pytest.mark.parametrize("route,field", [
    (route, field) for route, fields in sorted(_REQUIRED.items()) for field in fields
])
def test_bad_field_is_rejected_and_nothing_is_written(api, mongo, route, field, bad):
    body = {"userId": "alice", "projectId": "P9", "projectName": "Rover"}
    body[field] = bad
    before = _snapshot(mongo)

    response = api.post(route, json=body)

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_input", "field": field}
    assert _snapshot(mongo) == before


@pytest.mark.parametrize("bad", [{"$ne": ""}, 5, "", "   "], ids=repr)
def test_main_rejects_blank_user_id(api, bad):
    # Query strings are always str; only the blank values are reachable.
    if isinstance(bad, str):
        response = api.get("/main", query_string={"userId": bad})
        assert response.status_code == 400
        assert response.get_json() == {"error": "missing_parameter", "field": "userId"}
