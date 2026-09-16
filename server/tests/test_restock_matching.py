"""
Restock resolves its target item through itemIdentity.findMatchingItemKey
(D-03's full resolution order: exact, loose substring/prefix, ambiguous,
none), scoped to one household + one location.
"""

import datetime

import hardwareDatabase as hardwareDB


def _today():
    return datetime.date.today().isoformat()


def _future():
    return (datetime.date.today() + datetime.timedelta(days=30)).isoformat()


def _restock(api, **overrides):
    body = {
        "householdId": "H1",
        "userId": "alice",
        "location": "Fridge",
        "itemName": "Milk",
        "quantity": 1,
        "purchaseDate": _today(),
        "bestByDate": _future(),
    }
    body.update(overrides)
    return api.post("/api/inventory/restock", json=body)


def _get_inventory(api, householdId="H1", userId="alice"):
    return api.get(f"/api/inventory?householdId={householdId}&userId={userId}")


def test_case_and_whitespace_variant_merges_into_one_item(api):
    _restock(api, itemName="Milk", quantity=2)
    secondResponse = _restock(api, itemName="  milk ", quantity=3)
    assert secondResponse.status_code == 201

    fridgeItems = _get_inventory(api).get_json()["locations"]["Fridge"]
    assert len(fridgeItems) == 1
    assert fridgeItems[0]["capacity"] == 5
    assert len(fridgeItems[0]["batches"]) == 2


def test_loose_match_merges_and_keeps_original_display_name(api):
    _restock(api, itemName="Milk", quantity=2)
    secondResponse = _restock(api, itemName="Whole Milk", quantity=3)
    assert secondResponse.status_code == 201

    fridgeItems = _get_inventory(api).get_json()["locations"]["Fridge"]
    assert len(fridgeItems) == 1
    assert fridgeItems[0]["capacity"] == 5
    # Display name stays the first-seen spelling -- a loose match never
    # silently renames the household's item.
    assert fridgeItems[0]["itemName"] == "Milk"


def test_same_name_different_location_never_merges(api):
    _restock(api, itemName="Milk", location="Fridge", quantity=2)
    _restock(api, itemName="Milk", location="Freezer", quantity=3, bestByDate=None)

    locations = _get_inventory(api).get_json()["locations"]
    assert len(locations["Fridge"]) == 1
    assert locations["Fridge"][0]["capacity"] == 2
    assert len(locations["Freezer"]) == 1
    assert locations["Freezer"][0]["capacity"] == 3


def test_ambiguous_restock_creates_a_third_item_and_reports_candidates(api):
    _restock(api, itemName="Whole Milk", quantity=1)
    _restock(api, itemName="Skim Milk", quantity=1)

    thirdResponse = _restock(api, itemName="Milk", quantity=4)
    assert thirdResponse.status_code == 201

    body = thirdResponse.get_json()
    ambiguity = body["item"].get("matchAmbiguity")
    assert ambiguity is not None
    assert set(ambiguity) == {"whole milk", "skim milk"}

    fridgeItems = _get_inventory(api).get_json()["locations"]["Fridge"]
    assert len(fridgeItems) == 3

    # Both existing items keep their original quantities -- nothing merged.
    quantitiesByKey = {item["itemKey"]: item["capacity"] for item in fridgeItems}
    assert quantitiesByKey["whole milk"] == 1
    assert quantitiesByKey["skim milk"] == 1
    assert quantitiesByKey["milk"] == 4


def test_restock_into_empty_location_creates_new_item_without_error(api):
    response = _restock(api, itemName="Rice", location="Fridge", quantity=2)
    assert response.status_code == 201

    fridgeItems = _get_inventory(api).get_json()["locations"]["Fridge"]
    assert len(fridgeItems) == 1
    assert fridgeItems[0]["itemName"] == "Rice"


def test_restock_with_only_spaces_name_returns_400_and_writes_nothing(api):
    response = _restock(api, itemName="   ")
    assert response.status_code == 400

    fridgeItems = _get_inventory(api).get_json()["locations"]["Fridge"]
    assert fridgeItems == []


def test_two_households_restocking_same_name_stay_separate(api, mongo):
    db = mongo[hardwareDB.DB_NAME]
    db[hardwareDB.HOUSEHOLDS_COLLECTION].insert_one({"householdId": "H2", "users": ["carol"]})

    _restock(api, householdId="H1", userId="alice", itemName="Milk", quantity=2)
    _restock(api, householdId="H2", userId="carol", itemName="Milk", quantity=5)

    h1Items = _get_inventory(api, householdId="H1", userId="alice").get_json()["locations"]["Fridge"]
    h2Items = _get_inventory(api, householdId="H2", userId="carol").get_json()["locations"]["Fridge"]

    assert len(h1Items) == 1
    assert h1Items[0]["capacity"] == 2
    assert len(h2Items) == 1
    assert h2Items[0]["capacity"] == 5


def test_merged_batches_returned_in_fridge_consumption_order(api):
    _restock(api, itemName="Milk", quantity=2, bestByDate="2026-12-01")
    _restock(api, itemName="Whole Milk", quantity=3, bestByDate="2026-11-01")

    fridgeItems = _get_inventory(api).get_json()["locations"]["Fridge"]
    bestByDates = [batch["bestByDate"] for batch in fridgeItems[0]["batches"]]
    assert bestByDates == ["2026-11-01", "2026-12-01"]


def test_merged_batches_returned_in_freezer_consumption_order(api):
    _restock(
        api, itemName="Peas", location="Freezer", quantity=2,
        purchaseDate="2026-03-01", bestByDate=None,
    )
    _restock(
        api, itemName="Frozen Peas", location="Freezer", quantity=3,
        purchaseDate="2026-01-01", bestByDate=None,
    )

    freezerItems = _get_inventory(api).get_json()["locations"]["Freezer"]
    assert len(freezerItems) == 1
    purchaseDates = [batch["purchaseDate"] for batch in freezerItems[0]["batches"]]
    assert purchaseDates == ["2026-01-01", "2026-03-01"]
