"""Regression tests for CR-01: unvalidated householdId/userId/reservationId/
userName types allow NoSQL-operator injection that bypasses household
isolation.

request.get_json() decodes arbitrary JSON, so a client can POST a dict
(e.g. {"$ne": "..."}) in place of a plain string identifier. Mongo then
interprets that value as a query operator instead of an equality match,
which can match documents belonging to OTHER households. Each test here
seeds a second household (H2) that the requesting user ("alice") is not a
member of, then attempts the injection against each of the four mutating
inventory routes and asserts the request is rejected with H2's data left
completely untouched.
"""

import hardwareDatabase as hardwareDB
import projectsDatabase as projectsDB


def _seedOtherHousehold(mongo):
    """H2 belongs to "carol" only. alice (seeded by the `mongo` fixture as
    a member of H1) has no relationship to H2 and must never be able to
    read or mutate its stock. H2's only item ("SecretStash") lives in
    Pantry so a householdId-injection that widens the query to "any
    household's Pantry item named SecretStash" resolves deterministically
    onto H2, regardless of which household document the injected
    householdId happens to match during membership assertion.
    """
    db = mongo[hardwareDB.DB_NAME]
    db[hardwareDB.HOUSEHOLDS_COLLECTION].insert_one(
        {"householdId": "H2", "users": ["carol"]}
    )
    db[hardwareDB.ITEMS_COLLECTION].insert_one(
        {
            "householdId": "H2",
            "location": "Pantry",
            "itemKey": "secretstash",
            "itemName": "SecretStash",
            "batches": [
                {
                    "batchId": "seed-batch",
                    "quantity": 10,
                    "purchaseDate": "2026-06-01",
                    "bestByDate": None,
                    "createdAt": "2026-06-01T00:00:00+00:00",
                }
            ],
            "reservations": [],
            "capacity": 10,
            "reservedQuantity": 0,
        }
    )


def _rawItem(mongo, householdId, location, itemKey):
    db = mongo[hardwareDB.DB_NAME]
    return db[hardwareDB.ITEMS_COLLECTION].find_one(
        {"householdId": householdId, "location": location, "itemKey": itemKey}
    )


# --- Route-level: dict householdId across all four mutating routes --------


def test_restock_rejects_dict_householdId_and_writes_nothing(api, mongo):
    _seedOtherHousehold(mongo)

    response = api.post(
        "/api/inventory/restock",
        json={
            "householdId": {"$ne": "nope"},
            "userId": "alice",
            "location": "Pantry",
            "itemName": "SecretStash",
            "quantity": 1,
            "purchaseDate": "2026-06-01",
            "bestByDate": None,
        },
    )
    assert response.status_code in (400, 403)

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["capacity"] == 10
    assert len(raw["batches"]) == 1


def test_consume_rejects_dict_householdId_and_writes_nothing(api, mongo):
    _seedOtherHousehold(mongo)

    response = api.post(
        "/api/inventory/consume",
        json={
            "householdId": {"$ne": "nope"},
            "userId": "alice",
            "location": "Pantry",
            "itemName": "SecretStash",
            "quantity": 10,
        },
    )
    assert response.status_code in (400, 403)

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["capacity"] == 10
    assert raw["batches"][0]["quantity"] == 10


def test_consume_rejects_list_householdId_and_writes_nothing(api, mongo):
    _seedOtherHousehold(mongo)

    response = api.post(
        "/api/inventory/consume",
        json={
            "householdId": ["H2"],
            "userId": "alice",
            "location": "Pantry",
            "itemName": "SecretStash",
            "quantity": 10,
        },
    )
    assert response.status_code in (400, 403)

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["capacity"] == 10


def test_reserve_rejects_dict_householdId_and_writes_nothing(api, mongo):
    _seedOtherHousehold(mongo)

    response = api.post(
        "/api/inventory/reserve",
        json={
            "householdId": {"$ne": "nope"},
            "userId": "alice",
            "userName": "Alice",
            "location": "Pantry",
            "itemName": "SecretStash",
            "quantity": 5,
        },
    )
    assert response.status_code in (400, 403)

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["reservedQuantity"] == 0
    assert raw["reservations"] == []


def test_release_rejects_dict_householdId_and_writes_nothing(api, mongo):
    _seedOtherHousehold(mongo)
    db = mongo[hardwareDB.DB_NAME]
    db[hardwareDB.ITEMS_COLLECTION].update_one(
        {"householdId": "H2", "location": "Pantry", "itemKey": "secretstash"},
        {
            "$push": {
                "reservations": {
                    "reservationId": "carol-resv-1",
                    "userId": "carol",
                    "userName": "Carol",
                    "quantity": 2,
                    "createdAt": "2026-06-01T00:00:00+00:00",
                }
            },
            "$inc": {"reservedQuantity": 2},
        },
    )

    response = api.post(
        "/api/inventory/release",
        json={
            "householdId": {"$ne": "nope"},
            "userId": "alice",
            "reservationId": "carol-resv-1",
        },
    )
    assert response.status_code == 403

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["reservedQuantity"] == 2
    assert len(raw["reservations"]) == 1


# --- reservationId injection (removeReservation) ---------------------------


def test_remove_reservation_rejects_dict_reservationId_and_writes_nothing(mongo):
    _seedOtherHousehold(mongo)
    db = mongo[hardwareDB.DB_NAME]
    db[hardwareDB.ITEMS_COLLECTION].update_one(
        {"householdId": "H2", "location": "Pantry", "itemKey": "secretstash"},
        {
            "$push": {
                "reservations": {
                    "reservationId": "carol-resv-1",
                    "userId": "carol",
                    "userName": "Carol",
                    "quantity": 2,
                    "createdAt": "2026-06-01T00:00:00+00:00",
                }
            },
            "$inc": {"reservedQuantity": 2},
        },
    )

    try:
        hardwareDB.removeReservation(mongo, "H2", {"$ne": "nope"}, "carol")
        raised = False
    except hardwareDB.ReservationNotFoundError:
        raised = True
    assert raised

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["reservedQuantity"] == 2
    assert len(raw["reservations"]) == 1


def test_remove_reservation_rejects_list_reservationId_and_writes_nothing(mongo):
    _seedOtherHousehold(mongo)
    db = mongo[hardwareDB.DB_NAME]
    db[hardwareDB.ITEMS_COLLECTION].update_one(
        {"householdId": "H2", "location": "Pantry", "itemKey": "secretstash"},
        {
            "$push": {
                "reservations": {
                    "reservationId": "carol-resv-1",
                    "userId": "carol",
                    "userName": "Carol",
                    "quantity": 2,
                    "createdAt": "2026-06-01T00:00:00+00:00",
                }
            },
            "$inc": {"reservedQuantity": 2},
        },
    )

    try:
        hardwareDB.removeReservation(mongo, "H2", ["carol-resv-1"], "carol")
        raised = False
    except hardwareDB.ReservationNotFoundError:
        raised = True
    assert raised

    raw = _rawItem(mongo, "H2", "Pantry", "secretstash")
    assert raw["reservedQuantity"] == 2
    assert len(raw["reservations"]) == 1


# --- assertHouseholdMember: shared choke point ------------------------------


def test_assert_household_member_rejects_dict_householdId(mongo):
    try:
        projectsDB.assertHouseholdMember(mongo, {"$ne": "nope"}, "alice")
        raised = False
    except projectsDB.NotAHouseholdMemberError:
        raised = True
    assert raised


def test_assert_household_member_rejects_dict_userId(mongo):
    try:
        projectsDB.assertHouseholdMember(mongo, "H1", {"$ne": "nope"})
        raised = False
    except projectsDB.NotAHouseholdMemberError:
        raised = True
    assert raised


# --- userName injection (addReservation) ------------------------------------


def test_reserve_rejects_dict_userName_and_writes_nothing(api, mongo):
    api.post(
        "/api/inventory/restock",
        json={
            "householdId": "H1",
            "userId": "alice",
            "location": "Pantry",
            "itemName": "Rice",
            "quantity": 5,
            "purchaseDate": "2026-06-01",
            "bestByDate": None,
        },
    )

    response = api.post(
        "/api/inventory/reserve",
        json={
            "householdId": "H1",
            "userId": "alice",
            "userName": {"$ne": "nope"},
            "location": "Pantry",
            "itemName": "Rice",
            "quantity": 1,
        },
    )
    assert response.status_code == 400

    raw = _rawItem(mongo, "H1", "Pantry", "rice")
    assert raw["reservedQuantity"] == 0
    assert raw["reservations"] == []
