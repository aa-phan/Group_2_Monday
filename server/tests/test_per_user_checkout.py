"""Tests for per-PROJECT checkout accountability.

This went through two earlier designs before landing here (see
hardwareDatabase.py's module docstring for the full history):

1. Per-user only: any project member could check in units a *different*
   member checked out, even from a different project entirely -- too
   loose, and the original reported bug.
2. Per-(user, project): fixed the cross-project leak, but also stopped
   teammates on the SAME project from checking in for each other -- too
   strict, and itself reported as a bug.
3. Per-project (this file): any member of a project may check in units a
   teammate on that SAME project checked out -- accountability is shared
   at the project level -- but checking in through a DIFFERENT project
   (even one the same person also belongs to) is still rejected.
"""

import pytest

import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB


def _checkout(api, projectId, userId, hwSetName, quantity):
    return api.post(
        "/api/hardware/checkout",
        json={"projectId": projectId, "userId": userId, "hwSetName": hwSetName, "quantity": quantity},
    )


def _checkin(api, projectId, userId, hwSetName, quantity):
    return api.post(
        "/api/hardware/checkin",
        json={"projectId": projectId, "userId": userId, "hwSetName": hwSetName, "quantity": quantity},
    )


def _fetch(api, projectId, userId):
    return api.get(f"/api/hardware?projectId={projectId}&userId={userId}")


@pytest.fixture
def bob_in_project(mongo):
    """H1 is seeded with members alice and bob (see conftest.py's `mongo`
    fixture) -- nothing extra needed here beyond naming the fixture for
    readability at each test's seed_set call site.
    """
    return mongo


# ---------------------------------------------------------------------------
# Teammates on the SAME project share one accountability total
# ---------------------------------------------------------------------------


def test_a_teammate_can_check_in_units_a_different_member_of_the_same_project_checked_out(
    api, seed_set, bob_in_project
):
    seed_set("H1", "HWSet1", 10)
    _checkout(api, "H1", "alice", "HWSet1", 5)

    response = _checkin(api, "H1", "bob", "HWSet1", 5)

    assert response.status_code == 200
    hwSet = response.get_json()["hardwareSet"]
    assert hwSet["available"] == 10
    assert hwSet["myCheckedOut"] == 0


def test_the_user_who_checked_it_out_can_check_it_back_in(api, seed_set):
    seed_set("H1", "HWSet1", 10)
    _checkout(api, "H1", "alice", "HWSet1", 5)

    response = _checkin(api, "H1", "alice", "HWSet1", 5)

    assert response.status_code == 200
    hwSet = response.get_json()["hardwareSet"]
    assert hwSet["available"] == 10
    assert hwSet["myCheckedOut"] == 0


def test_a_teammate_can_check_in_up_to_the_projects_full_pooled_total(api, seed_set, bob_in_project):
    """alice checks out 5, bob checks out 3 -- H1's pooled total is 8. bob
    may check in all 8 himself, even though he personally only checked out
    3 -- accountability is shared at the project level, not per person.
    """
    seed_set("H1", "HWSet1", 20)
    _checkout(api, "H1", "alice", "HWSet1", 5)
    _checkout(api, "H1", "bob", "HWSet1", 3)

    response = _checkin(api, "H1", "bob", "HWSet1", 8)

    assert response.status_code == 200
    assert response.get_json()["hardwareSet"]["myCheckedOut"] == 0


def test_checking_in_more_than_the_projects_pooled_total_is_still_rejected(api, seed_set, bob_in_project):
    seed_set("H1", "HWSet1", 20)
    _checkout(api, "H1", "alice", "HWSet1", 5)
    _checkout(api, "H1", "bob", "HWSet1", 3)

    response = _checkin(api, "H1", "bob", "HWSet1", 9)

    assert response.status_code == 409
    body = response.get_json()
    assert body["error"] == "checkin_exceeds_checked_out"
    assert body["checkedOut"] == 8  # the project's pooled total, not either user's individual share
    assert body["requested"] == 9


# ---------------------------------------------------------------------------
# The shared total is visible to, and shared by, every member of the project
# ---------------------------------------------------------------------------


def test_two_members_of_the_same_project_see_the_same_pooled_total(api, seed_set, bob_in_project):
    seed_set("H1", "HWSet1", 20)
    _checkout(api, "H1", "alice", "HWSet1", 5)
    _checkout(api, "H1", "bob", "HWSet1", 3)

    aliceView = _fetch(api, "H1", "alice").get_json()["hardwareSets"][0]
    bobView = _fetch(api, "H1", "bob").get_json()["hardwareSets"][0]

    assert aliceView["available"] == bobView["available"] == 12
    assert aliceView["capacity"] == bobView["capacity"] == 20
    # Both teammates see the SAME pooled figure -- it belongs to the
    # project, not to either one of them individually.
    assert aliceView["myCheckedOut"] == bobView["myCheckedOut"] == 8


def test_checking_out_more_after_already_holding_some_adds_to_the_running_total(api, seed_set):
    seed_set("H1", "HWSet1", 20)
    _checkout(api, "H1", "alice", "HWSet1", 2)
    response = _checkout(api, "H1", "alice", "HWSet1", 3)

    assert response.get_json()["hardwareSet"]["myCheckedOut"] == 5


def test_either_teammates_checkin_reduces_the_one_shared_total(api, seed_set, bob_in_project):
    seed_set("H1", "HWSet1", 20)
    _checkout(api, "H1", "alice", "HWSet1", 5)
    _checkout(api, "H1", "bob", "HWSet1", 3)

    response = _checkin(api, "H1", "alice", "HWSet1", 2)

    assert response.status_code == 200
    assert response.get_json()["hardwareSet"]["myCheckedOut"] == 6  # 8 - 2, the shared total

    bobView = _fetch(api, "H1", "bob").get_json()["hardwareSets"][0]
    assert bobView["myCheckedOut"] == 6  # bob sees alice's checkin too


def test_a_teammate_who_never_personally_checked_anything_out_still_sees_the_full_shared_total(
    api, seed_set, bob_in_project
):
    seed_set("H1", "HWSet1", 10)
    _checkout(api, "H1", "alice", "HWSet1", 4)

    bobView = _fetch(api, "H1", "bob").get_json()["hardwareSets"][0]
    assert bobView["myCheckedOut"] == 4


# ---------------------------------------------------------------------------
# Direct hardwareDatabase-level coverage (not just through the route layer)
# ---------------------------------------------------------------------------


def test_checkin_by_a_teammate_on_the_same_project_succeeds_at_the_db_level(mongo, seed_set):
    seed_set("H1", "HWSet1", 10)
    hardwareDB.checkoutHardware(mongo, "H1", "HWSet1", 5, "alice")

    result = hardwareDB.checkinHardware(mongo, "H1", "HWSet1", 5, "bob")

    assert result["myCheckedOut"] == 0
    assert result["available"] == 10


def test_checkin_exceeds_checked_out_error_carries_the_projects_pooled_holding(mongo, seed_set):
    seed_set("H1", "HWSet1", 10)
    hardwareDB.checkoutHardware(mongo, "H1", "HWSet1", 5, "alice")

    with pytest.raises(hardwareDB.CheckinExceedsCheckedOutError) as caught:
        hardwareDB.checkinHardware(mongo, "H1", "HWSet1", 6, "bob")

    assert caught.value.checkedOut == 5
    assert caught.value.requested == 6


def test_checkedOutBy_rejects_a_non_string_userId(mongo, seed_set):
    seed_set("H1", "HWSet1", 10)
    with pytest.raises(hardwareDB.InvalidInventoryInput) as caught:
        hardwareDB.checkoutHardware(mongo, "H1", "HWSet1", 1, {"$ne": "alice"})
    assert str(caught.value) == "userId"


def test_get_project_hardware_status_reports_the_shared_project_total_to_every_member(
    mongo, seed_set, bob_in_project
):
    seed_set("H1", "HWSet1", 10)
    hardwareDB.checkoutHardware(mongo, "H1", "HWSet1", 4, "alice")

    aliceStatus = projectsDB.getProjectHardwareStatus(mongo, "H1", "alice")
    bobStatus = projectsDB.getProjectHardwareStatus(mongo, "H1", "bob")

    assert aliceStatus[0]["myCheckedOut"] == 4
    assert bobStatus[0]["myCheckedOut"] == 4


# ---------------------------------------------------------------------------
# Accountability is per PROJECT, not just per user -- the hardware catalog
# is global (shared by every project), but a checkout made through one
# project is a loan THAT PROJECT is accountable for, not a number floating
# free of any project or shared catalog-wide. Reported bug this section
# pins: alice is a member of both H1 and H2, checks out 5 units through H1,
# and should NOT be able to check those same 5 back in while acting through
# H2 -- even though it is the same person and the same global hardware set.
# ---------------------------------------------------------------------------


@pytest.fixture
def alice_in_two_projects(mongo):
    """H1 (alice, bob) comes from conftest.py's `mongo` fixture; add H2 with
    alice as its only member so she belongs to two projects at once.
    """
    mongo[hardwareDB.DB_NAME][hardwareDB.PROJECTS_COLLECTION].insert_one(
        {"householdId": "H2", "users": ["alice"]}
    )
    return mongo


def test_a_checkout_made_through_one_project_cannot_be_checked_in_through_another(
    api, seed_set, alice_in_two_projects
):
    seed_set("H1", "HWSet1", 10)
    _checkout(api, "H1", "alice", "HWSet1", 5)

    response = _checkin(api, "H2", "alice", "HWSet1", 5)

    assert response.status_code == 409
    body = response.get_json()
    assert body["error"] == "checkin_exceeds_checked_out"
    assert body["checkedOut"] == 0  # H2's own holding, not H1's 5
    assert body["requested"] == 5


def test_the_same_checkout_can_be_checked_in_through_the_project_it_was_made_through(
    api, seed_set, alice_in_two_projects
):
    seed_set("H1", "HWSet1", 10)
    _checkout(api, "H1", "alice", "HWSet1", 5)

    response = _checkin(api, "H1", "alice", "HWSet1", 5)

    assert response.status_code == 200
    assert response.get_json()["hardwareSet"]["myCheckedOut"] == 0


def test_myCheckedOut_is_scoped_to_the_project_being_viewed_through(api, seed_set, alice_in_two_projects):
    seed_set("H1", "HWSet1", 10)
    _checkout(api, "H1", "alice", "HWSet1", 5)

    throughH1 = _fetch(api, "H1", "alice").get_json()["hardwareSets"][0]
    throughH2 = _fetch(api, "H2", "alice").get_json()["hardwareSets"][0]

    assert throughH1["myCheckedOut"] == 5
    assert throughH2["myCheckedOut"] == 0
    # The global pool itself is unaffected by which project is asking.
    assert throughH1["available"] == throughH2["available"] == 5


def test_checking_out_the_same_set_through_two_different_projects_tracks_independently(
    api, seed_set, alice_in_two_projects
):
    seed_set("H1", "HWSet1", 20)
    _checkout(api, "H1", "alice", "HWSet1", 5)
    _checkout(api, "H2", "alice", "HWSet1", 3)

    throughH1 = _fetch(api, "H1", "alice").get_json()["hardwareSets"][0]
    throughH2 = _fetch(api, "H2", "alice").get_json()["hardwareSets"][0]

    assert throughH1["myCheckedOut"] == 5
    assert throughH2["myCheckedOut"] == 3
    assert throughH1["available"] == throughH2["available"] == 12

    # Checking in through H2 only ever touches the H2 entry.
    checkinResponse = _checkin(api, "H2", "alice", "HWSet1", 3)
    assert checkinResponse.status_code == 200
    assert _fetch(api, "H1", "alice").get_json()["hardwareSets"][0]["myCheckedOut"] == 5
    assert _fetch(api, "H2", "alice").get_json()["hardwareSets"][0]["myCheckedOut"] == 0
