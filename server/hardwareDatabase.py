# Import necessary libraries and modules
import os
import re
import uuid
from datetime import datetime, timezone

from bson.objectid import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

'''
Structure of a Hardware Set entry (collection `HardwareSets`, one document
per hwSetKey, GLOBAL across every project -- not partitioned per project).

Per course-staff feedback: projects do not own their own private stock.
There is one shared hardware catalog; every project's members check in/out/
request against the same sets. A project member is never allowed to mint a
new hardware set for "their" project -- hardwareDatabase.createHardwareSet
exists for seeding the global catalog (a one-time admin/script action, see
README.md), but no route or UI exposes it to an ordinary member any more.

HardwareSet = {
    '_id': ObjectId,
    'projectId': projectId,  # historical only: whichever project's create
                              # call happened to insert this document first.
                              # Never read for access control or filtering --
                              # see getHardwareStatus below. Kept only so a
                              # legacy document still has the field.
    'hwSetKey': normalizeHwSetName(hwSetName),
    'hwSetName': hwSetName,             # display name as last typed (create or rename)
    'active': bool,                     # False = deactivated; a MISSING field reads as active
    'capacity': int,                    # fixed total units; never changed by checkin/checkout
    'checkedOut': int,                  # units currently checked out, project-wide (0..capacity)
    'checkedOutBy': [
        {
            'userId': userId,
            'projectId': projectId,     # the project the checkout was made THROUGH
            'quantity': int,            # this (userId, projectId) pair's running total
        },
        ...
    ],                                   # at most one entry per (userId, projectId) pair
    'reservations': [
        {
            'reservationId': str,       # uuid4 hex
            'userId': userId,
            'userName': userName,
            'quantity': int,
            'createdAt': ISO-8601 str,
        },
        ...
    ],
    'reservedQuantity': int,            # maintained sum of reservations
}

This is the generic HaaS resource-management model from the assignment's
Figure 3 mockup: a project owns any number of named hardware sets (e.g.
HWSet1, HWSet2), each showing Capacity / Available, with Request (reserve),
Checkout, and Checkin actions. There is no storage location, no freshness,
and no per-restock batch history -- those were a prior domain-specific
extension that has been removed.

Deactivating a set (setHardwareSetActive) is refused while any units are
checked out, and a deactivated set refuses new checkouts and new requests.
Check-in and releasing an existing request stay available so nobody is
stranded holding units. Reactivating restores normal use. Rename changes
only the labels (hwSetName / hwSetKey); every internal write pins _id or
reservationId, so it is safe at any time.

`available` (capacity - checkedOut) is derived on read and never stored.
Requests (reservations) are a coordination signal only and never reduce it.

`checkedOutBy` is a per-(user, project) accountability ledger: Checkout is
still drawn from one global shared pool (gated by `checkedOut` against
`capacity`, same as before -- the catalog has no per-project allocation),
but Checkin is gated by what the CALLING user personally holds THROUGH THE
SAME PROJECT they're acting through, not the project-wide `checkedOut`
total and not even that same user's holding under a *different* project.
Checking out 5 units while acting through project A, then trying to check
them in while acting through project B, fails exactly like checking in
units you never personally checked out at all -- project is part of who
"owns" a checkout, not just an access-control lens on top of it. Without
this granularity, either any project member could check in units a
completely different member checked out (the bug per-user-only tracking
originally fixed), or the SAME member could check in through a project
they never checked anything out through (a bug this adds projectId to the
ledger entries to fix). An array of records (not a dynamic object keyed by
userId) on purpose: userId is arbitrary user input, and a `.` or a leading
`$` in a Mongo field key has special meaning -- exactly the kind of
value-vs-key injection risk `reservations` above and `assertProjectMember`
elsewhere in this codebase already avoid by storing userId as a field
*value*, never as a key.

This module holds ONLY the hardware-set store. Project membership lives in
the separate `Projects` collection (Track A owns writes to it); this module
reads nothing from it directly -- that is projectsDatabase's job via
assertProjectMember. Every function below still accepts a `projectId`
argument: it plays no part in WHICH hardware set is looked up (that's
hwSetKey alone, globally), but it IS part of the `checkedOutBy` ledger key
(see above) -- access to the catalog is membership-based
(assertProjectMember), never hardware-ownership-based, but a checkout's
accountability still remembers which project it was made through.
'''

DB_NAME = os.environ.get("MONGODB_DB", "HaaSResourceManager")
HARDWARE_SETS_COLLECTION = "HardwareSets"
PROJECTS_COLLECTION = "Households"

# Upper bound on any single quantity or capacity. MongoDB stores integers as
# at most 64 bits, so an unbounded value (or a running reservedQuantity sum
# of unbounded values) overflows inside the driver and surfaces as a 500.
MAX_QUANTITY = 2**31 - 1

_WHITESPACE_RUN = re.compile(r"\s+")


def _isValidQuantity(value):
    """True for a whole number from 1 to MAX_QUANTITY (booleans excluded)."""
    return not isinstance(value, bool) and isinstance(value, int) and 1 <= value <= MAX_QUANTITY


class InvalidInventoryInput(Exception):
    """Raised when checkin/checkout/request receives an invalid field. Maps to HTTP 400."""


class ItemNotFoundError(Exception):
    """Raised when an operation references a hardware set that does not exist. Maps to HTTP 404."""


class InsufficientStockError(Exception):
    """Raised when a checkout would exceed the hardware set's on-hand capacity.
    Maps to HTTP 409. Carries onHand (capacity read) and requested
    (quantity asked for) so the caller can report both.
    """

    def __init__(self, onHand, requested):
        self.onHand = onHand
        self.requested = requested
        super().__init__(
            "insufficient stock: onHand={} requested={}".format(onHand, requested)
        )


class HardwareSetNameTakenError(Exception):
    """Raised when a rename targets a name another set in the same project
    already uses. Maps to HTTP 409.
    """


class HardwareSetInactiveError(Exception):
    """Raised when a checkout or request targets a deactivated hardware set.
    Maps to HTTP 409.
    """


class HardwareSetInUseError(Exception):
    """Raised when a deactivate is refused because units are still checked
    out. Maps to HTTP 409. Carries checkedOut (the live count).
    """

    def __init__(self, checkedOut):
        self.checkedOut = checkedOut
        super().__init__("hardware set in use: checkedOut={}".format(checkedOut))


# $ne False matches True AND a missing field, so documents written before
# `active` existed behave as active with no migration.
_ACTIVE_GUARD = {"$ne": False}


class CheckinExceedsCheckedOutError(Exception):
    """Raised when a checkin would return more units than are currently
    checked out. Maps to HTTP 409. Carries checkedOut and requested.
    """

    def __init__(self, checkedOut, requested):
        self.checkedOut = checkedOut
        self.requested = requested
        super().__init__(
            "checkin exceeds checked out: checkedOut={} requested={}".format(checkedOut, requested)
        )


class ReservationNotFoundError(Exception):
    """Raised when releaseReservation cannot find an entry with the given
    reservationId at all (as opposed to one that exists but is owned by
    someone else). Maps to HTTP 404.
    """


class ReservationNotOwnedError(Exception):
    """Raised when releaseReservation finds a reservation with the given
    reservationId but it belongs to a different userId -- only the
    creating member can release their own claim. Maps to HTTP 403.
    Defined here (not in projectsDatabase.py) because hardwareDatabase is
    the module that detects the mismatch; projectsDatabase re-exports it
    for the route layer's error-mapping convenience.
    """


def normalizeHwSetName(rawName):
    """Normalize a raw hardware-set name into its hwSetKey.

    Strips leading/trailing whitespace, lowercases, and collapses every
    internal whitespace run to a single space. Exact match only after
    normalization -- no substring/fuzzy matching, unlike the old food-item
    identity resolver. A generic hardware-set name (e.g. "HWSet1") does not
    need loose matching; requiring an exact (case/whitespace-insensitive)
    name keeps checkin/checkout unambiguous.

    Raises:
        ValueError: if rawName is not a string, or normalizes to the empty
            string.
    """
    if not isinstance(rawName, str):
        raise ValueError("hwSetName must be a string")

    normalized = _WHITESPACE_RUN.sub(" ", rawName.strip()).lower()

    if normalized == "":
        raise ValueError("hwSetName must not be blank")

    return normalized


def _ensureHwSetUniqueIndex(collection):
    """Create the unique index backing checkinHardware's upsert.

    Global (hwSetKey alone, not per-project): a name identifies the same
    shared hardware set no matter which project's member is looking.
    Without a unique index, Mongo does not serialize two concurrent
    upserts that both target a never-before-seen hwSetKey with the same
    filter -- both can observe "no matching document" and both insert,
    silently splitting one hardware set's capacity across two documents.
    create_index is idempotent (a no-op once the index already exists), so
    calling it here on every call is safe and keeps this module
    self-contained without a separate migration step.
    """
    collection.create_index(
        "hwSetKey",
        unique=True,
        name="uniq_hwSetKey",
    )


def createHardwareSet(client, projectId, rawName, capacity):
    """Create a hardware set with a fixed `capacity` and nothing checked
    out. Idempotent: if the set already exists it is returned unchanged
    (capacity is never overwritten, and an inactive set stays inactive).

    Global catalog: hwSetKey alone identifies the set. `projectId` is
    stored only as a historical breadcrumb of whoever created it first --
    see this module's docstring -- and plays no part in the lookup, so
    creating "HWSet1" under a different projectId returns the SAME
    existing set, not a second one. Not reachable from any route any
    more; kept for admin/seeding use (README.md) only.
    """
    if not _isValidQuantity(capacity):
        raise InvalidInventoryInput("capacity")

    try:
        normalizedName = normalizeHwSetName(rawName)
    except ValueError:
        raise InvalidInventoryInput("hwSetName")

    collection = client[DB_NAME][HARDWARE_SETS_COLLECTION]
    _ensureHwSetUniqueIndex(collection)

    filter_ = {"hwSetKey": normalizedName}
    update = {
        "$setOnInsert": {
            "projectId": projectId,
            "hwSetKey": normalizedName,
            "hwSetName": rawName,
            "active": True,
            "capacity": capacity,
            "checkedOut": 0,
            "checkedOutBy": [],
            "reservations": [],
            "reservedQuantity": 0,
        },
    }

    try:
        doc = collection.find_one_and_update(
            filter_, update, upsert=True, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError:
        doc = collection.find_one_and_update(
            filter_, update, upsert=True, return_document=ReturnDocument.AFTER
        )

    return _serializeHardwareSet(doc)


def _resolveExistingHwSetKey(collection, rawName):
    """Resolve rawName to an existing hardware set's hwSetKey in the global
    catalog via exact normalized-name match. Raises ItemNotFoundError when
    there is no matching hardware set.
    """
    try:
        normalizedName = normalizeHwSetName(rawName)
    except ValueError:
        raise InvalidInventoryInput("hwSetName")

    doc = collection.find_one({"hwSetKey": normalizedName}, {"hwSetKey": 1})
    if doc is None:
        raise ItemNotFoundError(rawName)

    return normalizedName


def _adjustCheckedOut(client, projectId, rawName, quantity, userId, direction):
    """Shared checkin/checkout write. direction=+1 checks out, -1 checks in.

    `capacity` is never touched. Checkout is still gated by the project-wide
    `checkedOut` against `capacity`, as before -- anyone can draw from the
    shared pool. Checkin is gated by what userId personally holds THROUGH
    projectId specifically (the (userId, projectId) pair in `checkedOutBy`),
    NOT the project-wide total and NOT that same user's holding under a
    different project -- checking in more than you personally checked out
    THROUGH THIS PROJECT raises CheckinExceedsCheckedOutError even if the
    project-wide total would allow it, or even if you hold plenty under a
    different project.

    Every guard is re-applied inside the atomic find_one_and_update's filter
    itself, evaluated against the live document at write time -- not just
    the stale snapshot read at the top of the loop -- so two concurrent
    calls (checkout vs. checkout, checkin vs. checkin, same user or
    different users) can never push `checkedOut` outside 0..capacity or a
    single user's own `checkedOutBy` entry negative. When a write's filter
    doesn't match (another writer changed the live state first), the loop
    re-reads and retries against fresh data rather than failing outright.

    Checkout writes also carry the active guard, so a deactivate landing
    between the read and the write makes the write miss; the loop then
    re-reads and raises HardwareSetInactiveError instead of retrying
    forever. Checkin deliberately has no active guard.
    """
    if not _isValidQuantity(quantity):
        raise InvalidInventoryInput("quantity")
    if not isinstance(userId, str):
        # Same injection-safety reasoning as assertProjectMember/
        # removeReservation: userId lands in a Mongo filter below, and
        # request.get_json() can hand this function anything JSON allows.
        raise InvalidInventoryInput("userId")

    collection = client[DB_NAME][HARDWARE_SETS_COLLECTION]
    targetKey = _resolveExistingHwSetKey(collection, rawName)

    while True:
        doc = collection.find_one({"hwSetKey": targetKey})
        if doc is None:
            raise ItemNotFoundError(rawName)

        if direction > 0 and doc.get("active", True) is False:
            raise HardwareSetInactiveError(rawName)

        # capacity never changes after creation, so a stale read of it is safe.
        capacity = doc.get("capacity", 0)
        checkedOut = doc.get("checkedOut", 0)
        currentCheckedOutBy = doc.get("checkedOutBy", [])
        myEntry = next(
            (
                entry
                for entry in currentCheckedOutBy
                if entry.get("userId") == userId and entry.get("projectId") == projectId
            ),
            None,
        )
        myHolding = myEntry.get("quantity", 0) if myEntry is not None else 0

        if direction > 0:
            if quantity > capacity - checkedOut:
                raise InsufficientStockError(onHand=capacity - checkedOut, requested=quantity)
        else:
            # Gated by what THIS (user, project) pair holds -- not the
            # project-wide total, and not this same user's holding under a
            # different project.
            if quantity > myHolding:
                raise CheckinExceedsCheckedOutError(checkedOut=myHolding, requested=quantity)

        # Recompute the whole array in Python rather than updating one
        # element with a positional "$" operator. More than one entry can
        # now share a userId (one per project it was checked out through),
        # and resolving positional "$" against an $elemMatch condition that
        # only disambiguates entries by a NESTED field (projectId) is not
        # reliable under the mongomock version this project tests against
        # -- it can silently update the wrong array element (same class of
        # issue as the arrayFilters bug noted elsewhere in this module).
        if myEntry is not None:
            newCheckedOutBy = [
                dict(entry, quantity=entry["quantity"] + direction * quantity)
                if entry is myEntry
                else entry
                for entry in currentCheckedOutBy
            ]
        else:
            # Only reachable for direction > 0 (checkout): a checkin with
            # myHolding == 0 already raised above, since quantity is
            # always >= 1.
            newCheckedOutBy = currentCheckedOutBy + [
                {"userId": userId, "projectId": projectId, "quantity": quantity}
            ]

        # Pin the write on the EXACT array value just read (deep equality)
        # instead of a per-element filter -- the atomic optimistic-
        # concurrency guard this module uses everywhere else, just applied
        # to the whole array at once. Any concurrent change to ANY entry
        # (a different user's checkout, or this user's own entry under a
        # different project) makes this filter miss, so the loop re-reads
        # and retries against fresh data rather than silently overwriting
        # a write it never saw.
        filter_ = {"_id": doc["_id"], "checkedOutBy": currentCheckedOutBy}
        if direction > 0:
            # Checkout still needs the live capacity and active guards --
            # real, user-independent limits re-checked at write time.
            filter_["checkedOut"] = {"$lte": capacity - quantity}
            filter_["active"] = _ACTIVE_GUARD

        updated = collection.find_one_and_update(
            filter_,
            {
                "$inc": {"checkedOut": direction * quantity},
                "$set": {"checkedOutBy": newCheckedOutBy},
            },
            return_document=ReturnDocument.AFTER,
        )

        if updated is not None:
            return _serializeHardwareSet(updated, userId, projectId)


def renameHardwareSet(client, projectId, rawName, rawNewName, userId=None):
    """Rename a hardware set: hwSetName (display, stripped of surrounding
    whitespace) and hwSetKey change together. The unique index is the only
    collision check, so two racing renames cannot both win. Raises
    HardwareSetNameTakenError on a collision, ItemNotFoundError if the set
    does not exist.
    """
    try:
        currentKey = normalizeHwSetName(rawName)
    except ValueError:
        raise InvalidInventoryInput("hwSetName")
    try:
        newKey = normalizeHwSetName(rawNewName)
    except ValueError:
        raise InvalidInventoryInput("newName")

    collection = client[DB_NAME][HARDWARE_SETS_COLLECTION]
    # Otherwise only createHardwareSet makes this index, and without it the
    # collision would silently be allowed.
    _ensureHwSetUniqueIndex(collection)

    try:
        updated = collection.find_one_and_update(
            {"hwSetKey": currentKey},
            {"$set": {"hwSetKey": newKey, "hwSetName": rawNewName.strip()}},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        raise HardwareSetNameTakenError(rawNewName)

    if updated is None:
        raise ItemNotFoundError(rawName)

    return _serializeHardwareSet(updated, userId, projectId)


def setHardwareSetActive(client, projectId, rawName, active, userId=None):
    """Deactivate (active=False) or reactivate (active=True) a hardware set.
    Both are idempotent. Deactivating is refused with HardwareSetInUseError
    while any units are checked out.
    """
    if not isinstance(active, bool):
        raise InvalidInventoryInput("active")
    try:
        key = normalizeHwSetName(rawName)
    except ValueError:
        raise InvalidInventoryInput("hwSetName")

    collection = client[DB_NAME][HARDWARE_SETS_COLLECTION]
    base = {"hwSetKey": key}

    if active:
        updated = collection.find_one_and_update(
            base, {"$set": {"active": True}}, return_document=ReturnDocument.AFTER
        )
        if updated is None:
            raise ItemNotFoundError(rawName)
        return _serializeHardwareSet(updated, userId, projectId)

    while True:
        # $not $gt (not a literal 0): a document missing checkedOut must
        # still match, or the re-read below would loop forever.
        updated = collection.find_one_and_update(
            dict(base, checkedOut={"$not": {"$gt": 0}}),
            {"$set": {"active": False}},
            return_document=ReturnDocument.AFTER,
        )
        if updated is not None:
            return _serializeHardwareSet(updated, userId, projectId)

        doc = collection.find_one(base)
        if doc is None:
            raise ItemNotFoundError(rawName)
        if doc.get("checkedOut", 0) > 0:
            raise HardwareSetInUseError(doc.get("checkedOut", 0))
        # A concurrent check-in emptied the set; try the write again.


def checkinHardware(client, projectId, rawName, quantity, userId):
    """Check in (return) `quantity` units userId personally checked out
    THROUGH projectId specifically, raising availability. Raises
    CheckinExceedsCheckedOutError if this (userId, projectId) pair doesn't
    personally hold that many units -- even if the project-wide total
    checked out would otherwise allow it, or this same userId holds plenty
    under a different projectId.
    """
    return _adjustCheckedOut(client, projectId, rawName, quantity, userId, -1)


def checkoutHardware(client, projectId, rawName, quantity, userId):
    """Check out `quantity` units, lowering availability and crediting them
    to the (userId, projectId) pair's own `checkedOutBy` entry -- so they
    can only be checked back in through this same projectId. Raises
    InsufficientStockError (onHand = current availability) if more than
    are available. Outstanding requests never gate checkout.
    """
    return _adjustCheckedOut(client, projectId, rawName, quantity, userId, +1)


def addReservation(client, projectId, rawName, quantity, userId, userName):
    """Append a reservation entry (a "Request", per SN3) to the hardware set
    and increment reservedQuantity.

    Never compares quantity against capacity -- requesting beyond what is
    on hand is a legitimate thing for a project member to do; the
    overbooking guard applies to checkout only. Uses a single $push/$inc
    update so two simultaneous requests both survive rather than one
    overwriting the other.
    """
    if not _isValidQuantity(quantity):
        raise InvalidInventoryInput("quantity")

    # userName is stored directly into the reservation entry and echoed
    # back in API responses; reject anything but a string (or omitted)
    # rather than persisting a JSON object/array (defense-in-depth
    # alongside the projectId/userId/reservationId checks).
    if userName is not None and not isinstance(userName, str):
        raise InvalidInventoryInput("userName")

    db = client[DB_NAME]
    collection = db[HARDWARE_SETS_COLLECTION]

    targetKey = _resolveExistingHwSetKey(collection, rawName)

    reservationId = uuid.uuid4().hex
    reservation = {
        "reservationId": reservationId,
        "userId": userId,
        "userName": userName,
        "quantity": quantity,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    updated = collection.find_one_and_update(
        {"hwSetKey": targetKey, "active": _ACTIVE_GUARD},
        {
            "$push": {"reservations": reservation},
            "$inc": {"reservedQuantity": quantity},
        },
        return_document=ReturnDocument.AFTER,
    )

    if updated is None:
        # Either the set vanished or the active guard missed.
        if collection.find_one({"hwSetKey": targetKey}, {"_id": 1}) is None:
            raise ItemNotFoundError(rawName)
        raise HardwareSetInactiveError(rawName)

    return reservationId, _serializeHardwareSet(updated, userId, projectId)


def removeReservation(client, projectId, reservationId, userId):
    """Pull the reservation entry matching BOTH reservationId and userId,
    decrementing reservedQuantity by that entry's own quantity.

    When nothing is pulled, re-reads to distinguish the two failure
    cases: an entry with that reservationId owned by someone else raises
    ReservationNotOwnedError (403); no such entry at all raises
    ReservationNotFoundError (404).
    """
    # reservationId is used directly in a Mongo filter below; without this
    # check a dict/list value (request.get_json() decodes arbitrary JSON)
    # could be interpreted as a query operator instead of an equality
    # match. Treat a non-string reservationId the same as one that simply
    # doesn't exist.
    if not isinstance(reservationId, str):
        raise ReservationNotFoundError(reservationId)

    db = client[DB_NAME]
    collection = db[HARDWARE_SETS_COLLECTION]

    doc = collection.find_one({"reservations.reservationId": reservationId})

    if doc is None:
        raise ReservationNotFoundError(reservationId)

    entry = next(
        (
            reservation
            for reservation in doc.get("reservations", [])
            if reservation.get("reservationId") == reservationId
        ),
        None,
    )
    if entry is None:
        raise ReservationNotFoundError(reservationId)

    if entry.get("userId") != userId:
        raise ReservationNotOwnedError(reservationId)

    # Pin the write on the reservation still being present in the array,
    # not just on _id. Without this, a duplicate/concurrent release for
    # the same reservationId (e.g. a second browser tab, or a client
    # retry after a dropped response) can pass the ownership check above
    # twice -- each request reads its own copy of `entry` before either
    # writes -- and then both execute this update. The $pull is already
    # idempotent (a second pull matching nothing is a no-op), but without
    # this filter the $inc is unconditional and fires twice for one
    # logical release, double-decrementing reservedQuantity.
    updated = collection.find_one_and_update(
        {"_id": doc["_id"], "reservations.reservationId": reservationId},
        {
            "$pull": {"reservations": {"reservationId": reservationId}},
            "$inc": {"reservedQuantity": -entry.get("quantity", 0)},
        },
        return_document=ReturnDocument.AFTER,
    )

    if updated is None:
        # A losing duplicate/concurrent call: the reservation was already
        # pulled by the winning call between our read and this write.
        # Same outward result as "already released" (404), matching the
        # existing sequential double-release contract.
        raise ReservationNotFoundError(reservationId)

    return _serializeHardwareSet(updated, userId, projectId)


def getHardwareStatus(client, projectId, userId=None):
    """Return every hardware set in the GLOBAL catalog, sorted by display
    name for deterministic, repeatable ordering.

    projectId plays no part in which SETS come back -- every project's
    members see the exact same shared catalog, no per-project partition.
    It IS used, together with userId, to resolve each set's `myCheckedOut`
    figure to this (userId, projectId) pair's own holding -- see
    _serializeHardwareSet -- since a checkout made through a different
    project does not show up here.

    userId, when given, is whose personal `myCheckedOut` figure to include
    in each dict -- see _serializeHardwareSet. None (e.g. no acting user in
    context) simply omits it.
    """
    db = client[DB_NAME]
    collection = db[HARDWARE_SETS_COLLECTION]

    items = [_serializeHardwareSet(doc, userId, projectId) for doc in collection.find({})]
    items.sort(key=lambda item: item.get("hwSetKey", ""))
    return items


def _serializeHardwareSet(doc, userId=None, projectId=None):
    """Convert a raw Mongo document into a JSON-serializable hardware-set
    dict with `available` and `myCheckedOut` derived.

    The API boundary uses "request"/"requestId"/"requestedQuantity"/
    "available" (the assignment mockup's own Figure 3 vocabulary) even
    though the internal storage/implementation below this line keeps its
    original "reservation"/"availability" naming -- only this serializer
    and the /api/hardware/request+release routes in app.py know about the
    translation, so client and server agree on the wire format without a
    repo-wide rename of the underlying reservation machinery.

    `myCheckedOut` is the (userId, projectId) pair's own entry in
    `checkedOutBy` (0 if either is None, or there's no matching entry) --
    the number the client should actually cap a Check In control at for
    the project it's currently viewing, not the project-wide `available`/
    `checkedOut` figures (which say nothing about who personally holds
    what) and not this same user's holding under a *different* project.
    """
    capacity = doc.get("capacity", 0)
    checkedOut = doc.get("checkedOut", 0)
    reservedQuantity = doc.get("reservedQuantity", 0)
    requests = [
        {
            "requestId": reservation.get("reservationId"),
            "userId": reservation.get("userId"),
            "userName": reservation.get("userName"),
            "quantity": reservation.get("quantity"),
            "createdAt": reservation.get("createdAt"),
        }
        for reservation in doc.get("reservations", [])
    ]
    myEntry = next(
        (
            entry
            for entry in doc.get("checkedOutBy", [])
            if entry.get("userId") == userId and entry.get("projectId") == projectId
        ),
        None,
    )

    return {
        "_id": str(doc["_id"]) if isinstance(doc.get("_id"), ObjectId) else doc.get("_id"),
        "hwSetKey": doc.get("hwSetKey"),
        "hwSetName": doc.get("hwSetName"),
        "active": doc.get("active", True),
        "capacity": capacity,
        "requests": requests,
        "requestedQuantity": reservedQuantity,
        "available": max(capacity - checkedOut, 0),
        "myCheckedOut": myEntry.get("quantity", 0) if myEntry is not None else 0,
    }
