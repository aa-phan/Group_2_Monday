# Import necessary libraries and modules
import os
import uuid
from datetime import date, datetime, timezone

from bson.objectid import ObjectId
from pymongo import ReturnDocument

import freshness
from itemIdentity import normalizeItemName

'''
Structure of Item entry (collection `Items`, one document per
household + location + itemKey):

Item = {
    '_id': ObjectId,
    'householdId': householdId,
    'location': 'Pantry' | 'Fridge' | 'Freezer',
    'itemKey': normalizeItemName(itemName),
    'itemName': itemName,               # display name, first spelling used
    'batches': [
        {
            'batchId': str,             # uuid4 hex
            'quantity': int,
            'purchaseDate': 'YYYY-MM-DD',
            'bestByDate': 'YYYY-MM-DD' or None,
            'createdAt': ISO-8601 str,
        },
        ...
    ],
    'reservations': [],                 # populated by plan 02-04
    'capacity': int,                    # maintained sum of batch quantities
    'reservedQuantity': int,            # maintained sum of reservations; 0 here
}

`availability` (capacity - reservedQuantity, floored at 0) and `freshness`
(added by plan 02-02) are derived on read and never stored.

Per CONTEXT.md D-01, a restock always appends a NEW batch to the item; it
never increments an existing batch's quantity, even when its bestByDate is
identical to an existing batch's.

This module holds ONLY the item-stock store. Household membership lives in
the separate `Households` collection (Track A owns writes to it); this
module reads nothing from it directly — that is projectsDatabase's job via
assertHouseholdMember.
'''

DB_NAME = os.environ.get("MONGODB_DB", "PantryTrack")
ITEMS_COLLECTION = "Items"
HOUSEHOLDS_COLLECTION = "Households"
LOCATIONS = ("Pantry", "Fridge", "Freezer")

_DATE_FORMAT = "%Y-%m-%d"


class InvalidInventoryInput(Exception):
    """Raised when addBatch receives an invalid field. Maps to HTTP 400."""


class ItemNotFoundError(Exception):
    """Raised when an operation references an item that does not exist. Maps to HTTP 404."""


def _isValidDateString(value):
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, _DATE_FORMAT)
    except ValueError:
        return False
    return True


def addBatch(client, householdId, location, rawName, quantity, purchaseDate, bestByDate):
    """Append a new batch to the item identified by householdId+location+itemKey.

    Validates every field and raises InvalidInventoryInput naming the
    offending field on failure. Upserts the item document and increments
    its stored `capacity` by `quantity` in the same update.
    """
    if location not in LOCATIONS:
        raise InvalidInventoryInput("location")

    # bool is a subclass of int in Python; reject it explicitly.
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise InvalidInventoryInput("quantity")

    if not _isValidDateString(purchaseDate):
        raise InvalidInventoryInput("purchaseDate")

    if bestByDate is not None and not _isValidDateString(bestByDate):
        raise InvalidInventoryInput("bestByDate")

    try:
        itemKey = normalizeItemName(rawName)
    except ValueError:
        raise InvalidInventoryInput("itemName")

    db = client[DB_NAME]
    collection = db[ITEMS_COLLECTION]

    batch = {
        "batchId": uuid.uuid4().hex,
        "quantity": quantity,
        "purchaseDate": purchaseDate,
        "bestByDate": bestByDate,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    updated = collection.find_one_and_update(
        {"householdId": householdId, "location": location, "itemKey": itemKey},
        {
            "$push": {"batches": batch},
            "$inc": {"capacity": quantity},
            "$setOnInsert": {
                "householdId": householdId,
                "location": location,
                "itemKey": itemKey,
                "itemName": rawName,
                "reservations": [],
                "reservedQuantity": 0,
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    return _serializeItem(updated)


def getItemsByLocation(client, householdId):
    """Return a dict with exactly the three LOCATIONS keys, each mapping to
    a list of item dicts for that location, sorted for deterministic,
    repeatable ordering, and annotated with `freshness` on every item and
    every batch.

    `today` is computed once per call from the server's own clock -- never
    from a request parameter -- so a client cannot influence what freshness
    values come back. Freshness is added to the returned dicts only; it is
    never written back to MongoDB, since a stored flag would go stale the
    moment the calendar advances.
    """
    db = client[DB_NAME]
    collection = db[ITEMS_COLLECTION]

    today = date.today()
    result = {location: [] for location in LOCATIONS}

    for doc in collection.find({"householdId": householdId}):
        item = _serializeItem(doc)
        _annotateFreshness(item, today)
        result[item["location"]].append(item)

    for location in LOCATIONS:
        result[location].sort(key=lambda item: _itemSortKey(item, location))

    return result


def _annotateFreshness(item, today):
    """Add `freshness` to each batch and to the item itself, in place.
    Purely computed from the already-serialized dict; nothing here touches
    MongoDB, so nothing here is ever persisted.
    """
    location = item["location"]
    for batch in item["batches"]:
        batch["freshness"] = freshness.computeBatchFreshness(
            location, batch.get("purchaseDate"), batch.get("bestByDate"), today
        )
    item["freshness"] = freshness.computeItemFreshness(location, item["batches"], today)


def _batchSortKey(batch, location):
    """Sort key for batches within an item: bestByDate ascending for Pantry
    and Fridge, purchaseDate ascending for Freezer, createdAt as tie-break,
    with a None date sorting last.
    """
    if location == "Freezer":
        primaryDate = batch.get("purchaseDate")
    else:
        primaryDate = batch.get("bestByDate")

    # None dates sort last: (1, "") beats (0, actual-date-string).
    datePresence = 1 if primaryDate is None else 0
    return (datePresence, primaryDate or "", batch.get("createdAt") or "")


def _itemSortKey(item, location):
    """Sort key for items within a location: earliest batch date ascending,
    itemKey ascending as tie-break.
    """
    batches = item.get("batches") or []
    if batches:
        earliest = _batchSortKey(batches[0], location)
    else:
        earliest = (1, "", "")
    return (earliest, item.get("itemKey", ""))


def _serializeItem(doc):
    """Convert a raw Mongo document into a JSON-serializable item dict with
    batches sorted and `availability` derived.
    """
    location = doc.get("location")
    batches = sorted(doc.get("batches", []), key=lambda batch: _batchSortKey(batch, location))
    capacity = doc.get("capacity", 0)
    reservedQuantity = doc.get("reservedQuantity", 0)

    return {
        "_id": str(doc["_id"]) if isinstance(doc.get("_id"), ObjectId) else doc.get("_id"),
        "householdId": doc.get("householdId"),
        "location": location,
        "itemKey": doc.get("itemKey"),
        "itemName": doc.get("itemName"),
        "batches": batches,
        "reservations": doc.get("reservations", []),
        "capacity": capacity,
        "reservedQuantity": reservedQuantity,
        "availability": max(capacity - reservedQuantity, 0),
    }
