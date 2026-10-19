"""Project and membership logic in the DB modules (TD-05)."""

import pytest

import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB
import usersDatabase as usersDB

PASSWORD = "correct horse battery"


def _projectDoc(mongo, projectId):
    return mongo[hardwareDB.DB_NAME][hardwareDB.PROJECTS_COLLECTION].find_one(
        {"householdId": projectId}
    )


# ---------------------------------------------------------------------------
# projectsDB.createProject / queryProject
# ---------------------------------------------------------------------------


def test_create_project_stores_document_under_householdId(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc")

    stored = _projectDoc(mongo, "P9")
    assert stored["projectName"] == "Rover"
    assert stored["description"] == "desc"
    assert stored["users"] == []


def test_create_project_rejects_duplicate_id(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc")
    with pytest.raises(projectsDB.ProjectAlreadyExistsError):
        projectsDB.createProject(mongo, "Other", "P9", "")


def test_create_project_rejects_seeded_id(mongo):
    with pytest.raises(projectsDB.ProjectAlreadyExistsError):
        projectsDB.createProject(mongo, "Other", "H1", "")


def test_query_project_shape(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc")

    assert projectsDB.queryProject(mongo, "P9") == {
        "projectId": "P9",
        "projectName": "Rover",
        "description": "desc",
        "users": [],
    }


def test_query_project_tolerates_missing_fields(mongo):
    project = projectsDB.queryProject(mongo, "H1")

    assert project["projectName"] == ""
    assert project["description"] == ""
    assert project["users"] == ["alice", "bob"]
    assert "_id" not in project
    assert "householdId" not in project


@pytest.mark.parametrize("projectId", ["nope", {"$ne": ""}, 5, None])
def test_query_project_returns_none_for_unknown_or_non_str(mongo, projectId):
    assert projectsDB.queryProject(mongo, projectId) is None


# ---------------------------------------------------------------------------
# projectsDB.addUser / listProjectsForUser
# ---------------------------------------------------------------------------


def test_add_user_is_idempotent(mongo):
    projectsDB.createProject(mongo, "Rover", "P9", "desc")
    projectsDB.addUser(mongo, "P9", "carol")
    projectsDB.addUser(mongo, "P9", "carol")

    assert _projectDoc(mongo, "P9")["users"] == ["carol"]


def test_add_user_unknown_project(mongo):
    with pytest.raises(projectsDB.ProjectNotFoundError):
        projectsDB.addUser(mongo, "ghost", "carol")


def test_list_projects_for_user_sorted_summaries(mongo):
    projectsDB.createProject(mongo, "Zed", "P2", "z")
    projectsDB.createProject(mongo, "Rover", "P1", "r")
    projectsDB.addUser(mongo, "P2", "alice")
    projectsDB.addUser(mongo, "P1", "alice")

    assert projectsDB.listProjectsForUser(mongo, "alice") == [
        {"projectId": "H1", "projectName": "", "description": ""},
        {"projectId": "P1", "projectName": "Rover", "description": "r"},
        {"projectId": "P2", "projectName": "Zed", "description": "z"},
    ]


def test_list_projects_for_user_without_projects(mongo):
    assert projectsDB.listProjectsForUser(mongo, "nobody") == []


# ---------------------------------------------------------------------------
# usersDB.getUser
# ---------------------------------------------------------------------------


def test_get_user_omits_password(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)

    assert usersDB.getUser(mongo, "carol") == {
        "username": "Carol",
        "userId": "carol",
        "projects": [],
    }


@pytest.mark.parametrize("userId", ["ghost", {"$ne": ""}, 5, None])
def test_get_user_returns_none_for_unknown_or_non_str(mongo, userId):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)

    assert usersDB.getUser(mongo, userId) is None


# ---------------------------------------------------------------------------
# usersDB.joinProject / getUserProjectsList
# ---------------------------------------------------------------------------


def test_join_project_updates_both_sides_idempotently(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)
    projectsDB.createProject(mongo, "Rover", "P9", "desc")

    usersDB.joinProject(mongo, "carol", "P9")
    summary = usersDB.joinProject(mongo, "carol", "P9")

    assert summary["projectId"] == "P9"
    assert summary["users"] == ["carol"]
    assert usersDB.getUser(mongo, "carol")["projects"] == ["P9"]


def test_join_project_unknown_user(mongo):
    with pytest.raises(usersDB.UserNotFoundError):
        usersDB.joinProject(mongo, "ghost", "H1")


def test_join_project_unknown_project_writes_nothing(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)

    with pytest.raises(projectsDB.ProjectNotFoundError):
        usersDB.joinProject(mongo, "carol", "ghost")

    assert usersDB.getUser(mongo, "carol")["projects"] == []


def test_get_user_projects_list_matches_project_listing(mongo):
    usersDB.addUser(mongo, "Alice", "alice", PASSWORD)

    assert usersDB.getUserProjectsList(mongo, "alice") == (
        projectsDB.listProjectsForUser(mongo, "alice")
    )


def test_get_user_projects_list_unknown_user(mongo):
    with pytest.raises(usersDB.UserNotFoundError):
        usersDB.getUserProjectsList(mongo, "ghost")


def test_created_and_joined_project_passes_hardware_membership_guard(mongo):
    usersDB.addUser(mongo, "Carol", "carol", PASSWORD)
    projectsDB.createProject(mongo, "Rover", "P9", "desc")
    usersDB.joinProject(mongo, "carol", "P9")

    projectsDB.assertProjectMember(mongo, "P9", "carol")
