"""
Freshness annotation tests for the live inventory read path
(GET /api/inventory -> hardwareDatabase.getItemsByLocation).

Dates here use relative offsets from the real "today" (past/future by a
number of days), not pinned literals -- these tests only assert relative
freshness *categories* (expired / expiring_soon / fresh / unknown), which
hold regardless of which calendar day the suite happens to run on. The
exact boundary values (e.g. Fridge at precisely 3 days) are covered by
server/tests/test_freshness.py against a pinned today.
"""

import datetime

import freshness


def _today():
    return datetime.date.today().isoformat()


def _daysFromToday(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


def _restock(api, **overrides):
    body = {
        "householdId": "H1",
        "userId": "alice",
        "location": "Pantry",
        "itemName": "Oats",
        "quantity": 4,
        "purchaseDate": _today(),
        "bestByDate": _daysFromToday(30),
    }
    body.update(overrides)
    return api.post("/api/inventory/restock", json=body)


def _get_inventory(api, householdId="H1", userId="alice"):
    return api.get(f"/api/inventory?householdId={householdId}&userId={userId}")


def test_pantry_item_past_best_by_is_expired_at_item_and_batch_level(api):
    response = _restock(
        api, itemName="Stale Rice", location="Pantry", bestByDate=_daysFromToday(-5)
    )
    assert response.status_code == 201

    getResponse = _get_inventory(api)
    item = getResponse.get_json()["locations"]["Pantry"][0]
    assert item["freshness"] == freshness.EXPIRED
    assert item["batches"][0]["freshness"] == freshness.EXPIRED


def test_fridge_item_two_days_from_best_by_is_expiring_soon(api):
    response = _restock(
        api, itemName="Yogurt", location="Fridge", bestByDate=_daysFromToday(2)
    )
    assert response.status_code == 201

    getResponse = _get_inventory(api)
    item = getResponse.get_json()["locations"]["Fridge"][0]
    assert item["freshness"] == freshness.EXPIRING_SOON
    assert item["batches"][0]["freshness"] == freshness.EXPIRING_SOON


def test_freezer_item_purchased_400_days_ago_is_expired_regardless_of_best_by(api):
    response = _restock(
        api,
        itemName="Ground Beef",
        location="Freezer",
        purchaseDate=_daysFromToday(-400),
        bestByDate=_daysFromToday(365),
    )
    assert response.status_code == 201

    getResponse = _get_inventory(api)
    item = getResponse.get_json()["locations"]["Freezer"][0]
    assert item["freshness"] == freshness.EXPIRED
    assert item["batches"][0]["freshness"] == freshness.EXPIRED


def test_item_with_one_fresh_and_one_expired_batch_rolls_up_to_expired(api):
    _restock(api, itemName="Beans", location="Pantry", bestByDate=_daysFromToday(30))
    _restock(api, itemName="Beans", location="Pantry", bestByDate=_daysFromToday(-2))

    getResponse = _get_inventory(api)
    item = getResponse.get_json()["locations"]["Pantry"][0]
    assert item["freshness"] == freshness.EXPIRED

    batchFreshnessValues = {batch["freshness"] for batch in item["batches"]}
    assert batchFreshnessValues == {freshness.FRESH, freshness.EXPIRED}


def test_pantry_item_with_no_best_by_date_is_unknown(api):
    response = _restock(api, itemName="Salt", location="Pantry", bestByDate=None)
    assert response.status_code == 201

    getResponse = _get_inventory(api)
    item = getResponse.get_json()["locations"]["Pantry"][0]
    assert item["freshness"] == freshness.UNKNOWN
    assert item["batches"][0]["freshness"] == freshness.UNKNOWN


def test_location_with_no_items_is_an_empty_list_with_no_fabricated_freshness_key(api):
    getResponse = _get_inventory(api)
    locations = getResponse.get_json()["locations"]
    assert locations["Freezer"] == []


def test_freshness_is_never_persisted_on_the_raw_items_document(api, mongo):
    _restock(api, itemName="Oats", location="Pantry", bestByDate=_daysFromToday(-5))
    _get_inventory(api)

    import hardwareDatabase as hardwareDB

    db = mongo[hardwareDB.DB_NAME]
    rawDoc = db[hardwareDB.ITEMS_COLLECTION].find_one({"itemKey": "oats"})
    assert rawDoc is not None
    assert "freshness" not in rawDoc
    for batch in rawDoc["batches"]:
        assert "freshness" not in batch
