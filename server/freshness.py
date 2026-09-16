"""
Location-specific freshness rules (INV-05 / D-09, D-10, D-11).

Pure functions, standard library only -- no pymongo, no Flask, no network,
so this module can be reasoned about and tested in complete isolation from
the database and the HTTP layer. `today` is always passed in by the caller;
this module never reads the system clock itself.

Freezer's EXPIRED band is a freezer-burn / quality-degradation signal, NOT
a food-safety expiry like Pantry and Fridge. Frozen food past
FREEZER_EXPIRED_MONTHS is still safe to eat; it must be presented to the
household as a quality warning, never an instruction to discard. Do not
unify these three rule-sets into one parameterized rule -- they model
three physically different processes (dry staple shelf life, refrigerated
shelf life, freezer-burn quality decay) that only coincidentally share a
shape.

Freezer "whole months elapsed" is the calendar month difference between
`today` and `purchaseDate`, decremented by one if `today`'s day-of-month
has not yet reached `purchaseDate`'s day-of-month. server/tests/test_freshness.py
pins its dates against a fixed today (2026-06-15) using this exact
definition, so its boundary cases (exactly 6 months, exactly 12 months, one
day short of 6 months) agree with this implementation by construction.
"""

from datetime import datetime

FRESH = "fresh"
EXPIRING_SOON = "expiring_soon"
EXPIRED = "expired"
UNKNOWN = "unknown"

SEVERITY_RANK = {
    UNKNOWN: 0,
    FRESH: 1,
    EXPIRING_SOON: 2,
    EXPIRED: 3,
}

FRIDGE_EXPIRING_SOON_DAYS = 3
FREEZER_EXPIRING_SOON_MONTHS = 6
FREEZER_EXPIRED_MONTHS = 12

_DATE_FORMAT = "%Y-%m-%d"
_LOCATIONS = ("Pantry", "Fridge", "Freezer")


def _parseDate(value, fieldName):
    """Parse an ISO (YYYY-MM-DD) date string into a date object.

    Raises ValueError (naming the offending field) for anything that is
    not a well-formed ISO date string -- a malformed date must never fall
    through to a silent "fresh" default.
    """
    if not isinstance(value, str):
        raise ValueError(f"{fieldName} must be an ISO date string (YYYY-MM-DD), got {value!r}")
    try:
        return datetime.strptime(value, _DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"{fieldName} is not a valid ISO date string (YYYY-MM-DD): {value!r}")


def _wholeMonthsElapsed(purchaseDate, today):
    """Whole calendar months between purchaseDate and today."""
    months = (today.year - purchaseDate.year) * 12 + (today.month - purchaseDate.month)
    if today.day < purchaseDate.day:
        months -= 1
    return months


def _pantryFreshness(bestByDate, today):
    """D-09: fresh until the best-by date passes, then expired. No early
    warning window at all -- dry staples don't need one.
    """
    if bestByDate is None:
        return UNKNOWN
    bestBy = _parseDate(bestByDate, "bestByDate")
    return EXPIRED if bestBy < today else FRESH


def _fridgeFreshness(bestByDate, today):
    """D-10: expiring_soon within FRIDGE_EXPIRING_SOON_DAYS of the best-by
    date (inclusive), expired once the date has passed.
    """
    if bestByDate is None:
        return UNKNOWN
    bestBy = _parseDate(bestByDate, "bestByDate")
    if bestBy < today:
        return EXPIRED
    daysAway = (bestBy - today).days
    if daysAway <= FRIDGE_EXPIRING_SOON_DAYS:
        return EXPIRING_SOON
    return FRESH


def _freezerFreshness(purchaseDate, today):
    """D-11: computed entirely from purchaseDate -- bestByDate is never
    consulted. fresh under FREEZER_EXPIRING_SOON_MONTHS, expiring_soon
    from there through FREEZER_EXPIRED_MONTHS inclusive, expired strictly
    beyond. This is a freezer-burn quality band, not a safety expiry.
    """
    if purchaseDate is None:
        return UNKNOWN
    purchase = _parseDate(purchaseDate, "purchaseDate")
    monthsElapsed = _wholeMonthsElapsed(purchase, today)
    if monthsElapsed < FREEZER_EXPIRING_SOON_MONTHS:
        return FRESH
    if monthsElapsed <= FREEZER_EXPIRED_MONTHS:
        return EXPIRING_SOON
    return EXPIRED


def computeBatchFreshness(location, purchaseDate, bestByDate, today):
    """Compute the freshness of a single batch under its location's rule.

    Raises ValueError for an unrecognized location or a malformed date
    string on the date field the location actually uses.
    """
    if location not in _LOCATIONS:
        raise ValueError(f"unknown location: {location!r}")

    if location == "Pantry":
        return _pantryFreshness(bestByDate, today)
    if location == "Fridge":
        return _fridgeFreshness(bestByDate, today)
    return _freezerFreshness(purchaseDate, today)


def computeItemFreshness(location, batches, today):
    """Roll up an item's freshness as the worst freshness among its
    batches, ranked by SEVERITY_RANK (a total order), so the result never
    depends on batch iteration order. Returns UNKNOWN for an empty list.
    """
    worst = UNKNOWN
    for batch in batches:
        batchFreshness = computeBatchFreshness(
            location, batch.get("purchaseDate"), batch.get("bestByDate"), today
        )
        if SEVERITY_RANK[batchFreshness] > SEVERITY_RANK[worst]:
            worst = batchFreshness
    return worst
