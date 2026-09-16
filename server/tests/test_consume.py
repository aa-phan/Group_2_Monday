"""Tests for POST /api/inventory/consume (server/hardwareDatabase.consumeFromItem).

Covers the FIFO drain order (D-02), the overbooking guard reading `capacity`
rather than `availability` (D-06, D-07, board item TD-04), the fact that a
rejected consume leaves every batch byte-identical, and that reservations
never gate consumption (D-05).
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


# --- Drain order -------------------------------------------------------


def test_consume_drains_soonest_expiring_batch_first_fridge(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 3, "2026-06-01", "2026-06-10")
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01", "2026-06-18")

    response = _consume(api, "H1", "alice", "Fridge", "Yogurt", 2)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 6
    batches = {batch["bestByDate"]: batch["quantity"] for batch in item["batches"]}
    assert batches["2026-06-10"] == 1
    assert batches["2026-06-18"] == 5


def test_consume_removes_first_batch_entirely_when_exhausted(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 3, "2026-06-01", "2026-06-10")
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01", "2026-06-18")

    response = _consume(api, "H1", "alice", "Fridge", "Yogurt", 3)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 5
    assert len(item["batches"]) == 1
    assert item["batches"][0]["bestByDate"] == "2026-06-18"
    assert item["batches"][0]["quantity"] == 5


def test_consume_spills_into_second_batch(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 3, "2026-06-01", "2026-06-10")
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01", "2026-06-18")

    response = _consume(api, "H1", "alice", "Fridge", "Yogurt", 5)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 3
    assert len(item["batches"]) == 1
    assert item["batches"][0]["bestByDate"] == "2026-06-18"
    assert item["batches"][0]["quantity"] == 3


def test_consume_drains_both_batches_leaves_item_with_empty_batch_list(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 3, "2026-06-01", "2026-06-10")
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 5, "2026-06-01", "2026-06-18")

    response = _consume(api, "H1", "alice", "Fridge", "Yogurt", 8)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 0
    assert item["batches"] == []


def test_same_best_by_date_drains_earlier_created_batch_first(api, mongo):
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 2, "2026-06-01", "2026-06-10")
    _restock(api, "H1", "alice", "Fridge", "Yogurt", 4, "2026-06-05", "2026-06-10")

    response = _consume(api, "H1", "alice", "Fridge", "Yogurt", 2)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 4
    assert len(item["batches"]) == 1
    assert item["batches"][0]["purchaseDate"] == "2026-06-05"
    assert item["batches"][0]["quantity"] == 4


def test_freezer_drains_oldest_purchase_date_first_ignoring_best_by(api, mongo):
    _restock(api, "H1", "alice", "Freezer", "Peas", 3, "2026-05-01", "2026-06-01")
    _restock(api, "H1", "alice", "Freezer", "Peas", 5, "2026-01-01", "2027-01-01")

    response = _consume(api, "H1", "alice", "Freezer", "Peas", 2)
    assert response.status_code == 200
    item = response.get_json()["item"]
    batches = {batch["purchaseDate"]: batch["quantity"] for batch in item["batches"]}
    assert batches["2026-01-01"] == 3
    assert batches["2026-05-01"] == 3


# --- The overbooking guard ----------------------------------------------


def test_consume_exactly_capacity_succeeds_and_leaves_zero(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Rice", 5, "2026-06-01")

    response = _consume(api, "H1", "alice", "Pantry", "Rice", 5)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 0
    assert item["batches"] == []


def test_consume_capacity_plus_one_is_rejected_and_leaves_batches_unchanged(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Rice", 5, "2026-06-01")

    response = _consume(api, "H1", "alice", "Pantry", "Rice", 6)
    assert response.status_code == 409
    body = response.get_json()
    assert body["error"] == "insufficient_stock"
    assert body["onHand"] == 5
    assert body["requested"] == 6

    raw = _rawItem(mongo, "H1", "Pantry", "rice")
    assert raw["capacity"] == 5
    assert len(raw["batches"]) == 1
    assert raw["batches"][0]["quantity"] == 5


def test_consume_zero_is_rejected_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Rice", 5, "2026-06-01")

    response = _consume(api, "H1", "alice", "Pantry", "Rice", 0)
    assert response.status_code == 400
    raw = _rawItem(mongo, "H1", "Pantry", "rice")
    assert raw["capacity"] == 5


def test_consume_negative_is_rejected_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Rice", 5, "2026-06-01")

    response = _consume(api, "H1", "alice", "Pantry", "Rice", -1)
    assert response.status_code == 400
    raw = _rawItem(mongo, "H1", "Pantry", "rice")
    assert raw["capacity"] == 5


def test_consume_non_integer_is_rejected_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Rice", 5, "2026-06-01")

    response = _consume(api, "H1", "alice", "Pantry", "Rice", "two")
    assert response.status_code == 400
    raw = _rawItem(mongo, "H1", "Pantry", "rice")
    assert raw["capacity"] == 5


def test_consume_item_not_found_in_location_returns_404(api, mongo):
    response = _consume(api, "H1", "alice", "Pantry", "Rice", 1)
    assert response.status_code == 404
    body = response.get_json()
    assert body["error"] == "item_not_found"


# --- Reservations never gate consumption (D-05, D-06, D-07) -------------


def test_full_reservation_by_another_member_does_not_block_consume(api, mongo):
    item = _restock(api, "H1", "alice", "Pantry", "Beans", 3, "2026-06-01")
    itemKey = item["itemKey"]
    db = mongo[hardwareDB.DB_NAME]
    db[hardwareDB.ITEMS_COLLECTION].update_one(
        {"householdId": "H1", "location": "Pantry", "itemKey": itemKey},
        {
            "$push": {
                "reservations": {
                    "reservationId": "resv-1",
                    "userId": "bob",
                    "userName": "Bob",
                    "quantity": 3,
                    "createdAt": "2026-06-01T00:00:00+00:00",
                }
            },
            "$inc": {"reservedQuantity": 3},
        },
    )

    response = _consume(api, "H1", "alice", "Pantry", "Beans", 3)
    assert response.status_code == 200
    item = response.get_json()["item"]
    assert item["capacity"] == 0


# --- Not idempotent by design ---------------------------------------------


def test_two_identical_consumes_the_second_is_rejected(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Oats", 3, "2026-06-01")

    first = _consume(api, "H1", "alice", "Pantry", "Oats", 2)
    assert first.status_code == 200
    assert first.get_json()["item"]["capacity"] == 1

    second = _consume(api, "H1", "alice", "Pantry", "Oats", 2)
    assert second.status_code == 409
    body = second.get_json()
    assert body["onHand"] == 1
    assert body["requested"] == 2

    raw = _rawItem(mongo, "H1", "Pantry", "oats")
    assert raw["capacity"] == 1


# --- Membership guard -----------------------------------------------------


def test_consume_by_non_member_is_rejected_with_403_and_writes_nothing(api, mongo):
    _restock(api, "H1", "alice", "Pantry", "Rice", 5, "2026-06-01")

    response = _consume(api, "H1", "eve", "Pantry", "Rice", 1)
    assert response.status_code == 403
    raw = _rawItem(mongo, "H1", "Pantry", "rice")
    assert raw["capacity"] == 5
