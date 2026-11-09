"""Project and membership logic in the DB modules (TD-05).

Ported from PR #7 onto the PR #9 implementation of projectsDatabase.
"""

import contextlib

import pytest

import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB
import usersDatabase as usersDB

PASSWORD = "correct horse battery"


def _projectDoc(mongo, projectId):
    return mongo[hardwareDB.DB_NAME][hardwareDB.PROJECTS_COLLECTION].find_one(
        {"householdId": projectId}
    )


def _userDoc(mongo, userId):
    return mongo[usersDB.DB_NAME][usersDB.USERS_COLLECTION].find_one(
        {"userId": userId}
    )


# ---------------------------------------------------------------------------
# projectsDB.createProject / queryProject
# ---------------------------------------------------------------------------


def test_create_project_stores_document_under_householdId(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc", "carol")

    stored = _projectDoc(mongo, "P9")
    assert stored["projectName"] == "Rover"
    assert stored["description"] == "desc"
    assert stored["users"] == ["carol"]


def test_create_project_rejects_duplicate_id(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc", "carol")
    with pytest.raises(projectsDB.ProjectAlreadyExistsError):
        projectsDB.createProject(mongo, "Other", "P9", "other", "carol")


def test_create_project_rejects_seeded_id(mongo):
    with pytest.raises(projectsDB.ProjectAlreadyExistsError):
        projectsDB.createProject(mongo, "Other", "H1", "other", "carol")


def test_query_project_shape(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc", "carol")

    assert projectsDB.queryProject(mongo, "P9") == {
        "projectId": "P9",
        "projectName": "Rover",
        "description": "desc",
        "users": ["carol"],
    }


def test_query_project_tolerates_missing_fields(mongo):
    project = projectsDB.queryProject(mongo, "H1")

    assert project["projectName"] == ""
    assert project["description"] == ""
    assert project["users"] == ["alice", "bob"]
    assert "_id" not in project
    assert "householdId" not in project


def test_query_project_returns_none_for_unknown_id(mongo):
    assert projectsDB.queryProject(mongo, "nope") is None


@pytest.mark.parametrize("projectId", [{"$ne": ""}, 5, None, ""])
def test_query_project_rejects_non_str_or_empty_id(mongo, projectId):
    with pytest.raises(projectsDB.InvalidProjectInput) as excinfo:
        projectsDB.queryProject(mongo, projectId)

    assert str(excinfo.value) == "projectId"


# ---------------------------------------------------------------------------
# projectsDB.addUser / getUserProjects
# ---------------------------------------------------------------------------


def test_add_user_is_idempotent(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc", "dave")
    projectsDB.addUser(mongo, "P9", "carol")
    projectsDB.addUser(mongo, "P9", "carol")

    assert _projectDoc(mongo, "P9")["users"] == ["dave", "carol"]


def test_add_user_unknown_project(mongo):
    with pytest.raises(projectsDB.ProjectNotFoundError):
        projectsDB.addUser(mongo, "ghost", "carol")


def test_get_user_projects_sorted_by_project_id(mongo):
    projectsDB.createProject(mongo, "Zed", "P2", "z", "alice")
    projectsDB.createProject(mongo, "Rover", "P1", "r", "alice")

    assert projectsDB.getUserProjects(mongo, "alice") == [
        {
            "projectId": "H1",
            "projectName": "",
            "description": "",
            "users": ["alice", "bob"],
        },
        {
            "projectId": "P1",
            "projectName": "Rover",
            "description": "r",
            "users": ["alice"],
        },
        {
            "projectId": "P2",
            "projectName": "Zed",
            "description": "z",
            "users": ["alice"],
        },
    ]


def test_get_user_projects_without_projects(mongo):
    assert projectsDB.getUserProjects(mongo, "nobody") == []


# ---------------------------------------------------------------------------
# usersDB.joinProject / getUserProjectsList
# ---------------------------------------------------------------------------


def test_join_project_updates_membership_idempotently(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)
    projectsDB.createProject(mongo, "Rover", "P9", "desc", "dave")

    assert usersDB.joinProject(mongo, "carol", "P9") is None
    assert usersDB.joinProject(mongo, "carol", "P9") is None

    assert _projectDoc(mongo, "P9")["users"] == ["dave", "carol"]


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="B5: joinProject never checks the Users collection, so a userId with no account becomes a project member",
)
def test_join_project_unknown_user(mongo):
    # The suppress exists so the test turns XPASS (and strict fails it)
    # whichever exception a future fix chooses to raise.
    with contextlib.suppress(Exception):
        usersDB.joinProject(mongo, "ghost", "H1")

    assert "ghost" not in _projectDoc(mongo, "H1")["users"]


def test_join_project_unknown_project_writes_nothing(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)

    with pytest.raises(projectsDB.ProjectNotFoundError):
        usersDB.joinProject(mongo, "carol", "ghost")

    assert _userDoc(mongo, "carol")["projects"] == []
    assert _projectDoc(mongo, "ghost") is None


def test_get_user_projects_list_matches_project_listing(mongo):
    usersDB.addUser(mongo, "Alice", "alice", PASSWORD)

    assert usersDB.getUserProjectsList(mongo, "alice") == (
        projectsDB.getUserProjects(mongo, "alice")
    )


def test_get_user_projects_list_unknown_user_is_empty(mongo):
    assert usersDB.getUserProjectsList(mongo, "ghost") == []


def test_created_and_joined_project_passes_hardware_membership_guard(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)
    projectsDB.createProject(mongo, "Rover", "P9", "desc", "dave")
    usersDB.joinProject(mongo, "carol", "P9")

    projectsDB.assertProjectMember(mongo, "P9", "carol")
