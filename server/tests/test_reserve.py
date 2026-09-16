"""Tests for POST /api/inventory/reserve and POST /api/inventory/release
(server/hardwareDatabase.addReservation, removeReservation).

Covers D-04 (reserve and consume are independent), D-05/D-07 (reserve is
an unenforced flag -- overbooking is allowed, the guard applies to
consume only), and D-08 (a reservation can be released only by the
member who created it).
"""

import hardwareDatabase as hardwareDB


def _restock(api, householdId, userId, location, itemName, quantity, purchaseDate, bestByDate=None):
    response = api.post(
        "/api/inventory/restock",
        json={
            "householdId": householdId,
            "userId": userId,
            "location": location,
            "itemName": itemName,
            "quantity": quantity,
            "purchaseDate": purchaseDate,
            "bestByDate": bestByDate,
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["item"]


def _reserve(api, householdId, userId, userName, location, itemName, quantity):
    return api.post(
        "/api/inventory/reserve",
        json={
            "householdId": householdId,
            "userId": userId,
            "userName": userName,
            "location": location,
            "itemName": itemName,
            "quantity": quantity,
        },
    )


def _release(api, householdId, userId, reservationId):
    return api.post(
        "/api/inventory/release",
        json={"householdId": householdId, "userId": userId, "reservationId": reservationId},
    )


def _consume(api, householdId, userId, location, itemName, quantity):
    return api.post(
        "/api/inventory/consume",
        json={
            "householdId": householdId,
            "userId": userId,
            "location": location,
            "itemName": itemName,
            "quantity": quantity,
        },
    )


def _rawItem(mongo, householdId, location, itemKey):
    db = mongo[hardwareDB.DB_NAME]
    return db[hardwareDB.ITEMS_COLLECTION].find_one(
        {"householdId": householdId, "location": location, "itemKey": itemKey}
    )


# --- Reserving --------------------------------------------------------


def test_reserve_two_of_five_reports_reserved_and_availability(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2)
    assert response.status_code == 201
    body = response.get_json()
    assert "reservationId" in body
    item = body["item"]
    assert item["reservedQuantity"] == 2
    assert item["availability"] == 3
    assert item["capacity"] == 5


def test_reserve_response_carries_reserving_members_identity(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2)
    item = response.get_json()["item"]
    reservations = item["reservations"]
    assert len(reservations) == 1
    assert reservations[0]["userId"] == "alice"
    assert reservations[0]["userName"] == "Alice"
    assert reservations[0]["quantity"] == 2


def test_reserve_full_capacity_succeeds(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 5)
    assert response.status_code == 201
    item = response.get_json()["item"]
    assert item["availability"] == 0
    assert item["capacity"] == 5


def test_reserve_more_than_capacity_succeeds_availability_floored_at_zero(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 9)
    assert response.status_code == 201
    item = response.get_json()["item"]
    assert item["availability"] == 0
    assert item["capacity"] == 5
    assert item["reservedQuantity"] == 9


def test_reserve_zero_is_rejected_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 0)
    assert response.status_code == 400
    raw = _rawItem(mongo, "H1", "Fridge", "yogurt")
    assert raw["reservedQuantity"] == 0
    assert raw["reservations"] == []


def test_reserve_negative_is_rejected_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", -1)
    assert response.status_code == 400
    raw = _rawItem(mongo, "H1", "Fridge", "yogurt")
    assert raw["reservedQuantity"] == 0


def test_reserve_item_not_found_returns_404(api, mongo):
    response = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 1)
    assert response.status_code == 404
    assert response.get_json()["error"] == "item_not_found"


def test_same_member_reserving_twice_creates_two_separate_entries(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    first = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 1)
    second = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2)

    firstId = first.get_json()["reservationId"]
    secondId = second.get_json()["reservationId"]
    assert firstId != secondId

    item = second.get_json()["item"]
    assert item["reservedQuantity"] == 3
    assert len(item["reservations"]) == 2


def test_reservations_return_in_creation_order_stable_across_gets(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")
    _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 1)
    _reserve(api, "H1", "bob", "Bob", "Fridge", "Yogurt", 2)

    first = api.get("/api/inventory", query_string={"householdId": "H1", "userId": "alice"})
    second = api.get("/api/inventory", query_string={"householdId": "H1", "userId": "alice"})

    def _reservationIds(response):
        for item in response.get_json()["locations"]["Fridge"]:
            if item["itemKey"] == "yogurt":
                return [reservation["reservationId"] for reservation in item["reservations"]]
        return None

    idsFirst = _reservationIds(first)
    idsSecond = _reservationIds(second)
    assert idsFirst == idsSecond
    assert len(idsFirst) == 2


def test_two_members_reserving_same_item_both_survive(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    aliceReserve = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2)
    bobReserve = _reserve(api, "H1", "bob", "Bob", "Fridge", "Yogurt", 1)

    item = bobReserve.get_json()["item"]
    userIds = {reservation["userId"] for reservation in item["reservations"]}
    assert userIds == {"alice", "bob"}
    assert item["reservedQuantity"] == 3
    assert aliceReserve.status_code == 201


# --- Reserving never gates consuming (D-05) -------------------------------


def test_full_reservation_does_not_prevent_other_members_consume(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 3, "2026-06-01")
    _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 3)

    response = _consume(api, "H1", "bob", "Fridge", "Yogurt", 3)
    assert response.status_code == 200
    assert response.get_json()["item"]["capacity"] == 0


# --- Releasing --------------------------------------------------------


def test_creating_member_releases_reservation(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")
    reservationId = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2).get_json()[
        "reservationId"
    ]

    response = _release(api, "H1", "alice", reservationId)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["reservations"] == []
    assert item["reservedQuantity"] == 0
    assert item["capacity"] == 5


def test_different_member_cannot_release_reservation(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")
    reservationId = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2).get_json()[
        "reservationId"
    ]

    response = _release(api, "H1", "bob", reservationId)
    assert response.status_code == 403

    raw = _rawItem(mongo, "H1", "Fridge", "yogurt")
    assert len(raw["reservations"]) == 1
    assert raw["reservedQuantity"] == 2


def test_releasing_already_released_reservation_returns_404(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")
    reservationId = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2).get_json()[
        "reservationId"
    ]
    _release(api, "H1", "alice", reservationId)

    response = _release(api, "H1", "alice", reservationId)
    assert response.status_code == 404


def test_releasing_unknown_reservation_id_returns_404_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")

    response = _release(api, "H1", "alice", "does-not-exist")
    assert response.status_code == 404
    raw = _rawItem(mongo, "H1", "Fridge", "yogurt")
    assert raw["reservedQuantity"] == 0


def test_releasing_one_of_two_reservations_leaves_the_other_intact(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01")
    firstId = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 1).get_json()[
        "reservationId"
    ]
    secondId = _reserve(api, "H1", "alice", "Alice", "Fridge", "Yogurt", 2).get_json()[
        "reservationId"
    ]

    response = _release(api, "H1", "alice", firstId)
    assert response.status_code == 200
    item = response.get_json()["item"]
    remainingIds = [reservation["reservationId"] for reservation in item["reservations"]]
    assert remainingIds == [secondId]
    assert item["reservedQuantity"] == 2
