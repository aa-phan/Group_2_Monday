"""
Item identity helpers for the household inventory (Track B).

An item's identity within a household+location is derived from its display
name via normalization: strip leading/trailing whitespace, lowercase, and
collapse every internal whitespace run to a single space. The result is the
`itemKey` used to merge repeat restocks of the "same" item together.

Per CONTEXT.md D-03, item identity is normalization PLUS simple
substring/prefix matching -- and nothing more. `findMatchingItemKey`
implements the full D-03 resolution order (exact, then loose substring/
prefix with a single candidate, then ambiguous, then none) using plain
Python string containment in both directions.

Edit distance, stemming, and synonym matching are DELIBERATELY out of
scope. Do not "improve" this into difflib/rapidfuzz/fuzzywuzzy or a
synonym table -- D-03 draws this line explicitly so matching stays
predictable enough that a household can trust it, and an ambiguous match
(two or more equally-plausible existing items) always creates a new item
rather than guessing.
"""

import re

_WHITESPACE_RUN = re.compile(r"\s+")


class AmbiguousItemMatch(Exception):
    """Raised by findMatchingItemKey when a normalized name loosely matches
    two or more existing keys and there is no deterministic way to pick a
    winner. Carries the colliding keys, sorted, as `candidates`.
    """

    def __init__(self, candidates):
        self.candidates = sorted(candidates)
        super().__init__(
            "ambiguous match among candidates: {}".format(", ".join(self.candidates))
        )


def normalizeItemName(rawName):
    """Normalize a raw item name into its itemKey.

    Strips leading/trailing whitespace, lowercases, and collapses every
    internal whitespace run to a single space.

    Raises:
        ValueError: if rawName is not a string, or normalizes to the empty
            string.
    """
    if not isinstance(rawName, str):
        raise ValueError("itemName must be a string")

    normalized = _WHITESPACE_RUN.sub(" ", rawName.strip()).lower()

    if normalized == "":
        raise ValueError("itemName must not be blank")

    return normalized


def findMatchingItemKey(normalizedName, existingKeys):
    """Resolve normalizedName against an existing item's key within one
    household+location, per CONTEXT.md D-03's resolution order:

    1. exact  -- normalizedName is in existingKeys                -> return it
    2. loose  -- candidates are the keys where normalizedName is a substring
                 of the key, or the key is a substring of normalizedName
                 exactly one candidate                            -> return it
                 two or more candidates                           -> raise AmbiguousItemMatch
    3. none                                                       -> return None

    Uses plain Python string containment only -- no difflib, no regular
    expressions built from user input, no third-party matching library.
    The result never depends on the order of existingKeys.

    This function does NOT normalize its inputs -- the caller normalizes
    first (see normalizeItemName above). existingKeys is expected to
    already be normalized itemKeys.
    """
    if normalizedName in existingKeys:
        return normalizedName

    candidates = [
        key
        for key in existingKeys
        if normalizedName in key or key in normalizedName
    ]

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        raise AmbiguousItemMatch(candidates)

    return None
