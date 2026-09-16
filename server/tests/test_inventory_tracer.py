"""
End-to-end tracer test: restock-then-read through the Flask test client
against mongomock, covering the tracer path plus its boundaries.
"""

import datetime


def _today():
    return datetime.date.today().isoformat()


def _future():
    return (datetime.date.today() + datetime.timedelta(days=30)).isoformat()


def _restock(api, **overrides):
    body = {
        "householdId": "H1",
        "userId": "alice",
        "location": "Pantry",
        "itemName": "Oats",
        "quantity": 4,
        "purchaseDate": _today(),
        "bestByDate": _future(),
    }
    body.update(overrides)
    return api.post("/api/inventory/restock", json=body)


def _get_inventory(api, householdId="H1", userId="alice"):
    return api.get(f"/api/inventory?householdId={householdId}&userId={userId}")


def test_restock_then_read_shows_item_under_pantry(api):
    response = _restock(api, itemName="Oats", location="Pantry", quantity=4)
    assert response.status_code == 201

    getResponse = _get_inventory(api)
    assert getResponse.status_code == 200
    pantryItems = getResponse.get_json()["locations"]["Pantry"]
    assert len(pantryItems) == 1
    assert pantryItems[0]["itemName"] == "Oats"
    assert pantryItems[0]["capacity"] == 4
    assert pantryItems[0]["availability"] == 4


def test_second_restock_of_normalized_name_merges_into_one_item_with_two_batches(api):
    _restock(api, itemName="Oats", location="Pantry", quantity=4)
    secondResponse = _restock(api, itemName=" oats ", location="Pantry", quantity=3)
    assert secondResponse.status_code == 201

    getResponse = _get_inventory(api)
    pantryItems = getResponse.get_json()["locations"]["Pantry"]
    assert len(pantryItems) == 1
    assert pantryItems[0]["capacity"] == 7
    assert len(pantryItems[0]["batches"]) == 2


def test_same_name_different_location_is_a_separate_item(api):
    _restock(api, itemName="Oats", location="Pantry", quantity=4)
    _restock(api, itemName="Oats", location="Freezer", quantity=2)

    getResponse = _get_inventory(api)
    locations = getResponse.get_json()["locations"]

    assert len(locations["Pantry"]) == 1
    assert locations["Pantry"][0]["capacity"] == 4

    assert len(locations["Freezer"]) == 1
    assert locations["Freezer"][0]["capacity"] == 2


def test_empty_household_returns_all_three_location_keys_empty(api):
    getResponse = _get_inventory(api)
    assert getResponse.status_code == 200
    locations = getResponse.get_json()["locations"]

    assert set(locations.keys()) == {"Pantry", "Fridge", "Freezer"}
    assert locations["Pantry"] == []
    assert locations["Fridge"] == []
    assert locations["Freezer"] == []


def test_non_member_get_is_rejected_with_403_and_no_inventory(api):
    getResponse = _get_inventory(api, userId="mallory")
    assert getResponse.status_code == 403
    body = getResponse.get_json()
    assert body["error"] == "not_a_household_member"
    assert "locations" not in body


def test_restock_with_quantity_zero_is_rejected_and_writes_nothing(api):
    response = _restock(api, quantity=0)
    assert response.status_code == 400

    getResponse = _get_inventory(api)
    assert getResponse.get_json()["locations"]["Pantry"] == []


def test_restock_with_negative_quantity_is_rejected_and_writes_nothing(api):
    response = _restock(api, quantity=-1)
    assert response.status_code == 400

    getResponse = _get_inventory(api)
    assert getResponse.get_json()["locations"]["Pantry"] == []


def test_restock_with_blank_item_name_is_rejected_and_writes_nothing(api):
    response = _restock(api, itemName="   ")
    assert response.status_code == 400

    getResponse = _get_inventory(api)
    assert getResponse.get_json()["locations"]["Pantry"] == []


def test_restock_with_unknown_location_is_rejected_and_writes_nothing(api):
    response = _restock(api, location="Garage")
    assert response.status_code == 400

    getResponse = _get_inventory(api)
    locations = getResponse.get_json()["locations"]
    assert locations["Pantry"] == []
    assert "Garage" not in locations


def test_restock_with_missing_purchase_date_is_rejected_and_writes_nothing(api):
    response = _restock(api, purchaseDate=None)
    assert response.status_code == 400

    getResponse = _get_inventory(api)
    assert getResponse.get_json()["locations"]["Pantry"] == []


def test_two_consecutive_gets_of_unchanged_data_return_identical_ordering(api):
    _restock(api, itemName="Oats", location="Pantry", quantity=4)
    _restock(api, itemName="Barley", location="Pantry", quantity=2, bestByDate=_today())

    firstResponse = _get_inventory(api)
    secondResponse = _get_inventory(api)

    firstOrder = [item["itemKey"] for item in firstResponse.get_json()["locations"]["Pantry"]]
    secondOrder = [item["itemKey"] for item in secondResponse.get_json()["locations"]["Pantry"]]

    assert firstOrder == secondOrder
